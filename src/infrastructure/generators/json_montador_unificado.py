import json
import logging
from collections import defaultdict
import re
from src.utils.helpers import PathHelper

logger = logging.getLogger(__name__)

class JsonMontadorUnificado:
    """
    Classe unificada para montagem de JSON para Oracle e PostgreSQL,
    suportando tanto tabelas de contadores quanto de parâmetros.
    """
    
    def __init__(self, path_name, db_type='postgres', is_parameter=False, use_alerts=True):
        """
        Args:
            path_name: Caminho onde os JSONs serão salvos
            db_type: 'oracle' ou 'postgres'
            is_parameter: True para tabelas de parâmetros, False para contadores
            use_alerts: Se True, exibe diálogos; se False, não chama UI (para API/headless)
        """
        self.path_name = path_name
        self.db_type = db_type.lower()
        self.is_parameter = is_parameter
        self.use_alerts = use_alerts
        
        # Define o tipo de métrica baseado no modo
        self.metric_type = "PARAMETER" if is_parameter else "COUNTER"
        
        # Configurações específicas do banco de dados
        self._setup_db_config()
    
    def _setup_db_config(self):
        """Configura parâmetros específicos de cada banco de dados."""
        if self.db_type == 'oracle':
            self.config = {
                'case_transform': str.upper,
                'sql_types': {
                    'varchar': lambda size: f"VARCHAR2({size})" if size else "VARCHAR2",
                    'number': 'NUMBER',
                    'numeric20': 'NUMBER(20)',
                    'constant': 'VARCHAR2(3)',
                    'timestamp': 'TIMESTAMP'
                },
                'date_attribute': {
                    'sqlType': 'TIMESTAMP',
                    'toChar': "to_date(?,'YYYYMMDDHH24MI')",
                    'toDate': "to_date(?,'YYYYMMDDHH24MI')"
                },
                'sequence_type': 'NUMBER(20)'
            }

            if self.is_parameter:
                # Configuração específica para parâmetros Oracle
                self.config['date_attribute'] = {
                    'sqlType': 'TIMESTAMP',
                    'toChar': "to_char(?,'YYYY-MM-DD HH24:MI')",
                    'toDate': "TO_TIMESTAMP(?, 'YYYY-MM-DD HH24:MI:SS.FF')"
                }
        else:  # postgres
            self.config = {
                'case_transform': str.lower,
                'sql_types': {
                    'varchar': lambda size: f"varchar({size})" if size else "varchar",
                    'number': 'numeric',
                    'numeric20': 'numeric(20)',
                    'constant': 'VARCHAR2(3)',
                    'timestamp': 'timestamp'
                },
                'date_attribute': {
                    'sqlType': 'timestamp',
                    'toChar': "to_char(?,'YYYY-MM-DD HH24:MI')",
                    'toDate': "?::timestamp"
                },
                'sequence_type': 'numeric(20)'
            }

    def generate(self, data_sources_list, data_sources_attr_list):
        try:
            # Monta um dicionário {inventory_name: [linhas de atributos]}
            attr_dict = defaultdict(list)
            for row in data_sources_attr_list:
                attr_dict[row[0]].append(row)

            generated = 0
            skipped = []  # list of (inventory_name, reason)

            for ds_row in data_sources_list:
                inventory_name = ds_row[0]

                all_rows = attr_dict.get(inventory_name, [])
                if not all_rows:
                    reason = (
                        f"nenhuma linha encontrada na aba '3. Data Sources Attr & Count' "
                        f"para o Source Name '{inventory_name}'"
                    )
                    logger.warning(f"{inventory_name}: {reason}")
                    skipped.append((inventory_name, reason))
                    continue

                # Filtra atributos baseado no tipo (COUNTER ou PARAMETER)
                data_sources_attr_id = [
                    row for row in all_rows
                    if not (
                        (str(row[5]).strip().upper() == self.metric_type) or
                        (not self.is_parameter and (
                            str(row[5]).strip().upper() == 'INCREMENTAL/DECREMENTAL' or
                            str(row[6]).strip().upper() == 'INCREMENTAL/DECREMENTAL'
                        ))
                    )
                ]

                # Ordena a lista de atributos, colocando os que não são constantes no início
                data_sources_attr_id = sorted(
                    data_sources_attr_id,
                    key=lambda x: x[5].strip().upper() == 'CONSTANT'
                )

                # Cria uma lista com todos os atributos do tipo especificado
                data_sources_attr_counter = [
                    row for row in all_rows
                    if (
                        (str(row[5]).strip().upper() == self.metric_type) or
                        (not self.is_parameter and (
                            str(row[5]).strip().upper() == 'INCREMENTAL/DECREMENTAL' or
                            str(row[6]).strip().upper() == 'INCREMENTAL/DECREMENTAL'
                        ))
                    )
                ]

                # Se não há linhas do tipo de métrica esperado, não há o que gerar
                # (em modo PARAMETER precisamos de linhas Parameter; em modo COUNTER
                # precisamos de Counter ou INCREMENTAL/DECREMENTAL). idAttributes pode
                # ficar vazio sem problemas — tabelas só com Parameter caem nesse caso.
                if not data_sources_attr_counter:
                    tipo_msg = "Parameter" if self.is_parameter else "Counter / Incremental/Decremental"
                    reason = (
                        f"nenhuma linha com Metrics Attribute Type = {tipo_msg} "
                        f"em '3. Data Sources Attr & Count'"
                    )
                    logger.warning(f"{inventory_name}: {reason}")
                    skipped.append((inventory_name, reason))
                    continue

                # Extração e montagem do JSON
                table_name = ds_row[1]
                schema = ds_row[2]
                description = ds_row[3]
                period = ds_row[4]
                delay = ds_row[5]
                vendor = ds_row[6]
                tecnologiaGrupoDeContadores = ds_row[7].split("/")
                table_group = ds_row[8]

                # Aplica transformação de case apropriada
                case_func = self.config['case_transform']
                
                # O campo de tempo (DATETIME/RESULTTIME/...) pode estar em qualquer
                # linha de atributo do inventário, inclusive nas linhas marcadas como
                # Parameter (tabelas só-Parameter). Buscar em todas as linhas evita
                # cair no fallback "VERIFICAR QUAL O CAMPO DE TEMPO".
                date_attribute_name = self._verifica_tipo_tempo(all_rows)

                json_data = {
                    "tableInfo": {
                        "aditionalAttributes": self._infoAdicionalAttributes(data_sources_attr_id),
                        "counterNameColumn": "*",
                        "counterValueColumn": "*",
                        "dateAttribute": {
                            "name": date_attribute_name,
                            **self.config['date_attribute']
                        },
                        "dateAttributeUTC": {
                            "name": date_attribute_name,
                            **self.config['date_attribute']
                        },
                        "expirationDateAttribute": None,
                        "expirationDateAttributeUTC": None,
                        "partitionAttributes": None,
                        "dbn0Name": case_func(schema),
                        "delayMax": self._convert_to_seconds(delay),
                        "delayMin": self._convert_to_seconds(delay),
                        "description": description,
                        "eqTypeNameColumn": "*",
                        "hasDbn1Relation": False,
                        "hasSequence": True,
                        "idAttributes": self._idAttributes(data_sources_attr_id),
                        "inventoryAttributes": [],
                        "inventoryTypeName": inventory_name,
                        "metricAttributes": self._metricAttributes(data_sources_attr_counter),
                        "period": self._convert_to_seconds(period),
                        "sequenceAttribute": {
                            "name": "seq_number",
                            "sqlType": self.config['sequence_type']
                        },
                        "tableName": case_func(table_name),
                        "tableSchemaName": case_func(schema),
                        "timezoneMappingName": "",
                        "dataFilter": None,
                        "dataFilterType": "JEP",
                        "altSequenceAttribute": None,
                        "altDateTimeAttribute": None,
                        "altDateTimeAttributeUTC": None,
                        "altDateTimeSqlType": "TIMESTAMP",
                        "altUTCDateTimeSqlType": "TIMESTAMP",
                        "altTableName": "",
                        "measurementGroup": tecnologiaGrupoDeContadores[1],
                        "vendor": vendor,
                        "technology": tecnologiaGrupoDeContadores[0],
                        "consolidations": [""],
                        "discardNConsolidationDays": 0,
                        "dataTablespace": " ",
                        "indexTablespace": " ",
                        "isParameterTable": table_name.startswith("cm"),
                        "isDelta": None,
                        "externalMappings": []
                    },
                    "externalRelation": [],
                    "parentName": table_group
                }

                # Salvar JSON em arquivo com formatação correta
                json_path = f"{self.path_name}/{inventory_name}.json"
                self._save_json_with_formatting(json_path, json_data)
                generated += 1

            if skipped:
                logger.warning(
                    f"JSON: {generated} gerado(s), {len(skipped)} pulado(s). "
                    f"Pulados: {[name for name, _ in skipped]}"
                )
                for name, reason in skipped:
                    logger.warning(f"  - {name}: {reason}")

            self.skipped_inventories = skipped
            self.generated_count = generated
            return generated > 0

        except Exception as e:
            logger.error(f"Erro ao gerar JSON: {str(e)}")
            raise e

    def _save_json_with_formatting(self, json_path, json_data):
        """Salva o JSON com formatação especial para consolidations"""
        json_str = json.dumps(json_data, indent=4, ensure_ascii=False)
        
        # Corrige a formatação de consolidations para manter em uma única linha
        json_str = re.sub(
            r'"consolidations":\s*\[\s*\n\s*""\s*\n\s*\]',
            '"consolidations": [ "" ]',
            json_str
        )
        
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(json_str)

    def _build_attribute_dict(self, row, metricsAttributeType, example):
        """Constrói o dicionário de atributo padrão"""
        attributeCounterName = row[1]
        attributeCounterPhysicalName = row[2]
        dataType = row[3]
        
        return {
            "name": self._attributeCounterPhysicalName(attributeCounterPhysicalName, metricsAttributeType),
            "sqlType": self._dataType(dataType, metricsAttributeType),
            "counterDataMaxValue": 0,
            "counterDataMinValue": 0,
            "counterDataType": 0,
            "inventoryName": attributeCounterName,
            "inventoryType": self._inventoryType(dataType),
            "temporalAggregation": None,
            "spacialAggregation": None,
            "consolidated": False,
            "label": "",
            "fixedValue": "",
            "mappingName": "*",
            "semantics": "*",
            "defaultValue": example
        }

    def _idAttributes(self, data_sources_attr_id):
        """Retorna atributos ID e CONSTANT"""
        total = []

        for row in data_sources_attr_id:
            metricsAttributeType = row[5].upper()
            example = row[8]

            attr = self._build_attribute_dict(row, metricsAttributeType, example)

            if metricsAttributeType in ("ID", "CONSTANT"):
                total.append(attr)

        return total

    def _infoAdicionalAttributes(self, data_sources_attr_id):
        """Retorna atributos ADDITIONAL INFO"""
        total = []

        for row in data_sources_attr_id:
            metricsAttributeType = row[5].upper()
            example = row[8]

            attr = self._build_attribute_dict(row, metricsAttributeType, example)

            if metricsAttributeType.strip().upper() == "ADDITIONAL INFO":
                total.append(attr)

        return total

    def _metricAttributes(self, data_sources_attr_counter):
        """Retorna atributos de métricas (COUNTER ou PARAMETER)"""
        total = []

        for row in data_sources_attr_counter:
            AttributeCounterName = row[1]
            attributeCounterPhysicalName = row[2]
            dataType = row[3]

            attr = {
                "name": self._attributeCounterPhysicalName(attributeCounterPhysicalName, row[5]),
                "sqlType": self._dataType(dataType, row[5]),
                "counterDataMaxValue": 0,
                "counterDataMinValue": 0,
                "counterDataType": 0,
                "inventoryName": AttributeCounterName,
                "inventoryType": self._inventoryType(dataType),
                "temporalAggregation": "SUM",
                "spacialAggregation": "SUM",
                "consolidated": False,
                "label": AttributeCounterName
            }

            total.append(attr)

        return total

    def _inventoryType(self, data_type):
        """Traduz o tipo de dado para o tipo de inventário"""
        if not data_type:
            return "A definir"

        data_type = data_type.strip().upper()

        if data_type.startswith("VARCHAR"):
            return "String"
        elif data_type.startswith("NUMBER"):
            return "Double"
        else:
            return "A definir"

    def _attributeCounterPhysicalName(self, attributeCounterPhysicalName, metricsAttributeType):
        """Aplica transformação de case ao nome físico do atributo"""
        if metricsAttributeType.strip().upper() == "CONSTANT":
            return attributeCounterPhysicalName
        else:
            return self.config['case_transform'](attributeCounterPhysicalName)

    def _dataType(self, dataType, metricsAttributeType):
        """Converte tipo de dado para o formato específico do banco"""
        if metricsAttributeType.strip().upper() == "CONSTANT":
            return self.config['sql_types']['constant']
        if metricsAttributeType.strip().upper() == "INCREMENTAL/DECREMENTAL":
            return self.config['sql_types']['number']
        dataType = dataType.strip().upper()

        if dataType.startswith(("VARCHAR2", "VARCHAR", "CHAR")):
            match = re.search(r"\((.*?)\)", dataType)
            size = match.group(1) if match else None
            return self.config['sql_types']['varchar'](size)

        elif dataType.startswith("NUMBER"):
            return self.config['sql_types']['number']

        elif dataType.startswith("NUMERIC(20)"):
            return self.config['sql_types']['numeric20']

        # Para PostgreSQL, retorna lowercase por padrão
        return dataType.lower() if self.db_type == 'postgres' else dataType

    def _convert_to_seconds(self, time_str: str) -> int:
        """Converte strings de tempo para segundos"""
        if not time_str:
            return 0

        parts = time_str.strip().lower().split()

        if len(parts) != 2:
            raise ValueError(f"Formato inválido de tempo: '{time_str}' (esperado 'n unidade')")

        try:
            value = int(parts[0])
        except ValueError:
            raise ValueError(f"Valor numérico inválido no tempo: '{parts[0]}'")

        unit = parts[1].upper()

        if unit.startswith("MINUTE"):
            return value * 60
        elif unit.startswith("HOUR"):
            return value * 3600
        elif unit.startswith("DAY"):
            return value * 86400
        else:
            raise ValueError(f"Unidade de tempo desconhecida: '{unit}'")

    def _verifica_tipo_tempo(self, data_sources_attr_id):
        """Identifica o campo de tempo nos atributos"""
        elementos_row2 = [row[2] for row in data_sources_attr_id]

        # Lista de possíveis nomes de campos de tempo
        tipos_tempo = [
            "RESULTTIME",
            "STARTTIME",
            "COLLECTTIME",
            "MEASSTARTTIME",
            "DATETIME",
            "BEGINTIME"
        ]

        for valor in elementos_row2:
            if valor.upper() in tipos_tempo:
                return valor.upper()

        return "VERIFICAR QUAL O CAMPO DE TEMPO"