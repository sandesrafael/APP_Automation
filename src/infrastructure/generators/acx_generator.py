class ACXGenerator:

    def __init__(self, path_name):
        self.path_name = path_name

    def generate(self, inventory_name, data_sources_list, pk_list):
        ds_by_inv = {}
        for ds in data_sources_list:
            ds_by_inv.setdefault(ds[0], []).append(ds)

        pk_by_inv = {}
        for pk in pk_list:
            pk_by_inv.setdefault(pk[0], []).append(pk[1])

        for inv in inventory_name:
            lines = []
            lista_pk = pk_by_inv.get(inv, [])
            for ds in ds_by_inv.get(inv, []):
                lines.append(f"SEGNAME={ds[1]},\n")
                lines.append(f"    TABLENAME={ds[4].lower()}.{ds[1].lower()},\n")
                lines.append(f"    CONNECTION={ds[4].upper()},\n")
                if lista_pk:
                    lines.append(f"    KEY={'/'.join(lista_pk)}, $\n")
                else:
                    lines.append("    KEY=$\n")
            out_path = f"{self.path_name}/{inv.lower()}.acx"
            with open(out_path, "w", encoding="utf-8") as arquivo:
                arquivo.writelines(lines)