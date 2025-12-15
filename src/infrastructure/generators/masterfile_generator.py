from src.utils.helpers import DatabaseHelper
import logging

logger = logging.getLogger(__name__)

class MasterfileGenerator:
    def __init__(self, status, path_name, caminho_master):
        self.status = status  # True for Oracle, False for PostgreSQL
        self.path_name = path_name
        self.caminho_master = caminho_master
        
        # Configura parametros do banco de dados
        db_type = 'oracle' if status else 'postgres'
        self.db_config = DatabaseHelper.get_db_config(db_type)

    def generate(self, inventory_name, data_sources_list, data_sources_attr_list, data_sources_map_list, table_name_dic):
        ds_by_inv = {}
        for ds in data_sources_list:
            ds_by_inv.setdefault(ds[0], []).append(ds)

        dsa_by_inv = {}
        for dsa in data_sources_attr_list:
            dsa_by_inv.setdefault(dsa[0], []).append(dsa)

        dsm_by_inv_etn = {}
        for item in data_sources_map_list:
            inv = item[2]
            dsm_by_inv_etn.setdefault(inv, {}).setdefault(item[0], []).append(item)

        for inv in inventory_name:
            lines = []

            for ds in ds_by_inv.get(inv, []):
                suffix = self.db_config['suffix']
                alias_case = self.db_config['case_transform']
                if ds[2] != 'ENRICH':
                    lines.append(f"FILENAME={ds[1]}, SUFFIX={suffix}, REMARKS='{ds[3]}', $\n")
                    lines.append(f"  SEGMENT={ds[1]}, SEGTYPE=S0, $\n")
                    lines.append(f"FIELDNAME=SEQ_NUMBER, ALIAS={alias_case('SEQ_NUMBER')}, USAGE=P21, ACTUAL=P11, $\n")
                    lines.append(f"FIELDNAME=INSERT_DATE, ALIAS={alias_case('INSERT_DATE')}, USAGE=HYYMDS, ACTUAL=HYYMDS, $\n")
                    if self.db_config['uses_source_content']:
                        lines.append(f"FIELDNAME=SOURCE_ID, ALIAS={alias_case('SOURCE_ID')}, USAGE=A255V, ACTUAL=A255V, $\n")
                        lines.append(f"FIELDNAME=CONTENT_ID, ALIAS={alias_case('CONTENT_ID')}, USAGE=A256V, ACTUAL=A256V, $\n")
                else:
                    lines.append(f"FILENAME={ds[1]}, SUFFIX={suffix},\n")
                    lines.append(f"  SEGMENT={ds[1]}, SEGTYPE=S0, $\n")

            # Parte 2 — campos de atributos
            alias_case = self.db_config['case_transform']
            for dsa in dsa_by_inv.get(inv, []):
                alias = alias_case(dsa[2])
                if dsa[3] == "TIMESTAMP(3)" and dsa[5] != "Constant":
                    lines.append(
                        f"FIELDNAME={dsa[1].upper()}, ALIAS={alias}, TITLE='{dsa[1]}', DESCRIPTION='{dsa[6]}', USAGE=HYYMDS, ACTUAL=HYYMDS,\n    MISSING=ON, $\n"
                    )
                elif dsa[3].startswith("VARCHAR") and dsa[5] != "Constant":
                    lines.append(
                        f"FIELDNAME={dsa[1].upper()}, ALIAS={alias}, TITLE='{dsa[1]}', DESCRIPTION='{dsa[6]}', USAGE=A255V, ACTUAL=A255V,\n    MISSING=ON, $\n"
                    )
                elif dsa[3] == "NUMBER" and dsa[5] != "Constant":
                    lines.append(
                        f"FIELDNAME={dsa[1].upper()}, ALIAS={alias}, TITLE='{dsa[1]}', DESCRIPTION='{dsa[6]}', USAGE=D20.2, ACTUAL=D8,\n    MISSING=ON, $\n"
                    )

            # Parte 3 — segmentos e joins (agrupado por ETN, até 3 condições)
            etn_map = dsm_by_inv_etn.get(inv, {})
            for etn, items in etn_map.items():
                join_type = items[0][4].replace(' ', '_').upper()
                parent_table = table_name_dic[items[0][2]]
                crfile = f"{self.caminho_master}/{etn}" if self.caminho_master else etn

                def seg_cond(k):
                    return f"{parent_table}.{items[k][3].upper()} EQ {etn}.{items[k][1].upper()}"

                conds = [seg_cond(0)]
                if len(items) >= 2:
                    conds.append(seg_cond(1))
                if len(items) >= 3:
                    conds.append(seg_cond(2))
                join_where = " AND ".join(conds)

                lines.append(
                    f"SEGMENT={etn}, SEGTYPE=KU, PARENT={parent_table}, CRFILE={crfile}, CRINCLUDE=ALL, CRJOINTYPE={join_type}, JOIN_WHERE={join_where};,$\n"
                )

            out_path = f"{self.path_name}/{inv.lower()}.mas"
            with open(out_path, "w", encoding="utf-8") as arquivo:
                arquivo.writelines(lines)

    def _generate_part1(self, inventory_name, data_sources_list):
        for i in inventory_name:
            for ds in data_sources_list:
                if ds[0] == i:
                    self._generate_part1_oracle_or_postgre(ds)

    def _generate_part1_oracle_or_postgre(self, ds):
        with open(f"{self.path_name}/{ds[0].lower()}.mas", "a") as arquivo:
            suffix = self.db_config['suffix']
            alias_case = self.db_config['case_transform']

            if ds[2] != 'ENRICH':
                # Escreve as linhas comuns com as diferenças parametrizadas
                arquivo.write(f"FILENAME={ds[1]}, SUFFIX={suffix}, REMARKS='{ds[3]}', $\n")
                arquivo.write(f"  SEGMENT={ds[1]}, SEGTYPE=S0, $\n")
                # Campos comuns ajustando o ALIAS com base no banco de dados
                arquivo.write(f"FIELDNAME=SEQ_NUMBER, ALIAS={alias_case('SEQ_NUMBER')}, USAGE=P21, ACTUAL=P11, $\n")
                arquivo.write(f"FIELDNAME=INSERT_DATE, ALIAS={alias_case('INSERT_DATE')}, USAGE=HYYMDS, ACTUAL=HYYMDS, $\n")
                if self.db_config['uses_source_content']:
                    # Campos adicionais específicos para PostgreSQL
                    arquivo.write(f"FIELDNAME=SOURCE_ID, ALIAS={alias_case('SOURCE_ID')}, USAGE=A255V, ACTUAL=A255V, $\n")
                    arquivo.write(f"FIELDNAME=CONTENT_ID, ALIAS={alias_case('CONTENT_ID')}, USAGE=A256V, ACTUAL=A256V, $\n")
            else:
                # Caso ds[2] seja 'ENRICH'
                arquivo.write(f"FILENAME={ds[1]}, SUFFIX={suffix},\n")
                arquivo.write(f"  SEGMENT={ds[1]}, SEGTYPE=S0, $\n")

    def _generate_part2(self, inventory_name, data_sources_attr_list):
        for i in inventory_name:
            for dsa in data_sources_attr_list:
                if dsa[0] == i:
                    self._generate_part2_oracle_or_postgre(dsa)                      

    def _generate_part2_oracle_or_postgre(self, dsa):
        # Determina o ALIAS com base no banco de dados
        alias = self.db_config['case_transform'](dsa[2])

        with open(f"{self.path_name}/{dsa[0].lower()}.mas", "a") as arquivo:
            if dsa[3] == "TIMESTAMP(3)" and dsa[5] != "Constant":
                arquivo.write(
                    f"FIELDNAME={dsa[1].upper()}, ALIAS={alias}, TITLE='{dsa[1]}', "
                    f"DESCRIPTION='{dsa[6]}', USAGE=HYYMDS, ACTUAL=HYYMDS,\n    MISSING=ON, $\n"
                )
            elif dsa[3].startswith("VARCHAR") and dsa[5] != "Constant":
                arquivo.write(
                    f"FIELDNAME={dsa[1].upper()}, ALIAS={alias}, TITLE='{dsa[1]}', "
                    f"DESCRIPTION='{dsa[6]}', USAGE=A255V, ACTUAL=A255V,\n    MISSING=ON, $\n"
                )
            elif dsa[3] == "NUMBER" and dsa[5] != "Constant":
                arquivo.write(
                    f"FIELDNAME={dsa[1].upper()}, ALIAS={alias}, TITLE='{dsa[1]}', "
                    f"DESCRIPTION='{dsa[6]}', USAGE=D20.2, ACTUAL=D8,\n    MISSING=ON, $\n"
                )

    def _generate_part3_with_path_or_not(self, inventory_name, data_sources_map_list, table_name_dic):
        dsm = data_sources_map_list[:]
        for i in inventory_name:
            # Lista de ETNs relacionados ao inventário atual
            lista_ETN = [dsm_item[0] for dsm_item in dsm if dsm_item[2] == i]
            # Lista de ETNs únicos
            lista_ETN_uni = list(set(lista_ETN))
            # Lista com o ETN e a contagem de ocorrências
            lista_res = [(k, lista_ETN.count(k)) for k in lista_ETN_uni]

            for res in lista_res:
                for j, dsm_item in enumerate(dsm):
                    if dsm_item[2] == i and res[0] == dsm_item[0]:
                        try:
                            with open(f"{self.path_name}/{i.lower()}.mas", "a") as arquivo:
                                # Obtém o tipo de join, substituindo espaços por underscores e convertendo para maiúsculas
                                join_type = dsm_item[4].replace(' ', '_').upper()
                                # Nome da tabela pai
                                parent_table = table_name_dic[dsm_item[2]]

                                # Determina o CRFILE com base na presença de self.caminho_master
                                if self.caminho_master:
                                    # Correspondente à função _generate_part3_with_path
                                    crfile = f"{self.caminho_master}/{dsm_item[0]}"
                                else:
                                    # Correspondente à função _generate_part3_without_path
                                    crfile = dsm_item[0]

                                # Construção da cláusula JOIN_WHERE
                                join_where = f"{parent_table}.{dsm_item[3].upper()} EQ {dsm_item[0]}.{dsm_item[1].upper()}"
                                if res[1] >= 2:
                                    # Adiciona a segunda condição
                                    next_dsm_item = dsm[j + 1]
                                    join_where += f" AND {parent_table}.{next_dsm_item[3].upper()} EQ {dsm_item[0]}.{next_dsm_item[1].upper()}"
                                if res[1] == 3:
                                    # Adiciona a terceira condição
                                    next_dsm_item_2 = dsm[j + 2]
                                    join_where += f" AND {parent_table}.{next_dsm_item_2[3].upper()} EQ {dsm_item[0]}.{next_dsm_item_2[1].upper()}"

                                # Escreve no arquivo .mas
                                arquivo.write(
                                    f"SEGMENT={dsm_item[0]}, SEGTYPE=KU, PARENT={parent_table}, "
                                    f"CRFILE={crfile}, CRINCLUDE=ALL, "
                                    f"CRJOINTYPE={join_type}, JOIN_WHERE={join_where};,$\n"
                                )
                            break  # Sai do loop após escrever o segmento
                        except BaseException as e:
                            # Tratamento de exceções com mensagem de erro personalizada
                            logger.error(
                                f"Erro ao gerar masterfiles: Favor preencher as colunas 'DBN0 Attribute Physical Name', 'Enrichment Attribute Physical Name' e 'AdHoc Join Type' presentes na aba 3. Data Source Map. Erro: {e}",
                                exc_info=True
                            )
                            raise  # Relança a exceção para depuração