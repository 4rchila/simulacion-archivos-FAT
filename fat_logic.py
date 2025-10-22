import json
import os
from datetime import datetime
from typing import List, Optional

class FATManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.path_fat = os.path.join(self.data_dir, "fat_table.json")
        self.path_bloques = os.path.join(self.data_dir, "bloques")
        os.makedirs(self.path_bloques, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.path_fat):
            with open(self.path_fat, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4, ensure_ascii=False)

    def _leer_tabla_fat(self):
        with open(self.path_fat, "r", encoding="utf-8") as f:
            return json.load(f)

    def _guardar_tabla_fat(self, archivos):
        with open(self.path_fat, "w", encoding="utf-8") as f:
            json.dump(archivos, f, indent=4, ensure_ascii=False)

    def listar_archivos(self) -> List[str]:
        archivos = self._leer_tabla_fat()
        return [a["nombre"] for a in archivos if not a.get("papelera", False)]

    def obtener_datos_papelera(self):
        archivos = self._leer_tabla_fat()
        return [a for a in archivos if a.get("papelera", False)]

    def obtener_metadatos(self, nombre: str) -> Optional[dict]:
        archivos = self._leer_tabla_fat()
        return next((a for a in archivos if a["nombre"] == nombre), None)

    def separar_por_bloque(self, contenido: str, nombre: str) -> str:
        tamano_bloque = 20
        bloques = [contenido[i:i + tamano_bloque] for i in range(0, len(contenido), tamano_bloque)]
        rutas = []
        for i, bloque in enumerate(bloques):
            eof = (i == len(bloques) - 1)
            siguiente = None
            if not eof:
                siguiente = os.path.join(self.path_bloques, f"{nombre}_bloque{i+1}.json")
            datos_bloque = {"datos": bloque, "siguiente": siguiente, "eof": eof}
            ruta_archivo = os.path.join(self.path_bloques, f"{nombre}_bloque{i}.json")
            with open(ruta_archivo, "w", encoding="utf-8") as f:
                json.dump(datos_bloque, f, indent=3, ensure_ascii=False)
            rutas.append(ruta_archivo)
        if not rutas:
            ruta_vacia = os.path.join(self.path_bloques, f"{nombre}_bloque0.json")
            datos_bloque = {"datos": "", "siguiente": None, "eof": True}
            with open(ruta_vacia, "w", encoding="utf-8") as f:
                json.dump(datos_bloque, f, indent=3, ensure_ascii=False)
            return ruta_vacia
        return rutas[0]

    def crear_archivo(self, nombre: str, contenido: str, owner: str, permisos_por_rol: List[str]):
        ruta_inicial = self.separar_por_bloque(contenido, nombre)
        ahora = datetime.now().isoformat(sep=" ", timespec="seconds")
        nuevo = {
            "nombre": nombre,
            "ruta_inicial": ruta_inicial,
            "papelera": False,
            "tamaño": len(contenido),
            "fecha_creacion": ahora,
            "fecha_modificacion": None,
            "fecha_eliminacion": None,
            "owner": owner,
            "permisos": {owner: permisos_por_rol.copy()}
        }
        archivos = self._leer_tabla_fat()
        if any(a["nombre"] == nombre for a in archivos):
            raise ValueError(f"Ya existe un archivo con el nombre '{nombre}'.")
        archivos.append(nuevo)
        self._guardar_tabla_fat(archivos)

    def _concatenar_bloques(self, ruta_inicial: str) -> str:
        contenido_total = ""
        ruta_actual = ruta_inicial
        while ruta_actual:
            if not os.path.exists(ruta_actual):
                break
            with open(ruta_actual, "r", encoding="utf-8") as bloque_file:
                bloque = json.load(bloque_file)
                contenido_total += bloque.get("datos", "")
                ruta_actual = bloque.get("siguiente")
                if bloque.get("eof", False):
                    break
        return contenido_total

    def leer_archivo(self, nombre: str, rol: str) -> str:
        archivo = self.obtener_metadatos(nombre)
        if not archivo or archivo.get("papelera", False):
            raise FileNotFoundError(f"El archivo '{nombre}' no existe o está en la papelera.")
        permisos = archivo.get("permisos", {})
        if rol != archivo.get("owner") and "leer" not in permisos.get(rol, []):
            raise PermissionError("No tienes permiso para leer este archivo.")
        contenido = self._concatenar_bloques(archivo["ruta_inicial"])
        return contenido

    def eliminar_archivo(self, nombre: str):
        archivos = self._leer_tabla_fat()
        encontrado = False
        for a in archivos:
            if a["nombre"] == nombre and not a.get("papelera", False):
                a["papelera"] = True
                a["fecha_eliminacion"] = datetime.now().isoformat(sep=" ", timespec="seconds")
                encontrado = True
        if not encontrado:
            raise FileNotFoundError(f"Archivo '{nombre}' no encontrado o ya en papelera.")
        self._guardar_tabla_fat(archivos)

    def recuperar_archivo(self, nombre: str):
        archivos = self._leer_tabla_fat()
        encontrado = False
        for a in archivos:
            if a["nombre"] == nombre and a.get("papelera", False):
                a["papelera"] = False
                a["fecha_eliminacion"] = None
                encontrado = True
        if not encontrado:
            raise FileNotFoundError(f"Archivo '{nombre}' no encontrado en la papelera.")
        self._guardar_tabla_fat(archivos)

    def _eliminar_bloques_fisicos(self, nombre: str):
        prefijo = f"{nombre}_bloque"
        for fname in os.listdir(self.path_bloques):
            if fname.startswith(prefijo):
                try:
                    os.remove(os.path.join(self.path_bloques, fname))
                except Exception:
                    pass

    def modificar_archivo(self, nombre: str, nuevo_contenido: str, rol: str):
        archivos = self._leer_tabla_fat()
        archivo = next((a for a in archivos if a["nombre"] == nombre and not a.get("papelera", False)), None)
        if not archivo:
            raise FileNotFoundError(f"El archivo '{nombre}' no existe o está en la papelera.")
        permisos = archivo.get("permisos", {})
        if rol != archivo.get("owner") and "escribir" not in permisos.get(rol, []):
            raise PermissionError("No tienes permiso para modificar este archivo.")
        self._eliminar_bloques_fisicos(nombre)
        nueva_ruta = self.separar_por_bloque(nuevo_contenido, nombre)
        archivo["ruta_inicial"] = nueva_ruta
        archivo["tamaño"] = len(nuevo_contenido)
        archivo["fecha_modificacion"] = datetime.now().isoformat(sep=" ", timespec="seconds")
        self._guardar_tabla_fat(archivos)

    def asignar_permisos(self, nombre: str, solicitante_rol: str, rol_a_modificar: str, permisos: List[str]):
        archivos = self._leer_tabla_fat()
        archivo = next((a for a in archivos if a["nombre"] == nombre), None)
        if not archivo:
            return False, f"Archivo '{nombre}' no encontrado."
        if solicitante_rol != archivo.get("owner"):
            return False, "Solo el owner puede asignar o revocar permisos."
        if permisos:
            archivo.setdefault("permisos", {})[rol_a_modificar] = permisos.copy()
        else:
            if rol_a_modificar in archivo.get("permisos", {}):
                del archivo["permisos"][rol_a_modificar]
        self._guardar_tabla_fat(archivos)
        return True, "Permisos actualizados correctamente."
