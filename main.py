import tkinter as tk
from tkinter import messagebox, ttk
from fat_logic import FATManager
import json
import os

class LoginWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Inicio de Sesión - Sistema FAT")
        self.master.geometry("350x250")
        self.master.resizable(False, False)
        os.makedirs("data", exist_ok=True)
        usuarios_path = "data/usuarios.json"
        if not os.path.exists(usuarios_path):
            messagebox.showerror("Error", "No se encontró el archivo usuarios.json")
            master.destroy()
            return
        with open(usuarios_path, "r", encoding="utf-8") as f:
            self.permisos_globales = json.load(f)
        self.passwords = {"admin": "1234", "usuario": "abcd", "invitado": "0000"}
        tk.Label(master, text="Inicio de Sesión", font=("Arial", 14, "bold")).pack(pady=15)
        tk.Label(master, text="Selecciona tu rol:").pack(pady=5)
        self.combo_rol = ttk.Combobox(master, values=list(self.permisos_globales.keys()), state="readonly")
        self.combo_rol.pack(pady=5)
        self.combo_rol.current(0)
        tk.Label(master, text="Contraseña:").pack(pady=5)
        self.entry_pass = tk.Entry(master, show="*")
        self.entry_pass.pack(pady=5)
        tk.Button(master, text="Ingresar", command=self.verificar_login, width=12).pack(pady=15)

    def verificar_login(self):
        rol = self.combo_rol.get()
        password = self.entry_pass.get().strip()
        if rol in self.passwords and password == self.passwords[rol]:
            self.master.destroy()
            root = tk.Tk()
            acciones = self.permisos_globales[rol]
            app = InterfazFAT(root, rol, acciones, "data/usuarios.json")
            root.mainloop()
        else:
            messagebox.showerror("Error", "Contraseña incorrecta.")

class InterfazFAT:
    def __init__(self, master, rol, acciones, usuarios_path):
        self.master = master
        self.master.title(f"Simulador de Sistema FAT - {rol}")
        self.master.geometry("600x500")
        self.rol = rol
        self.acciones = acciones
        self.usuarios_path = usuarios_path
        with open(usuarios_path, "r", encoding="utf-8") as a:
            self.permisos_globales = json.load(a)
        self.fat = FATManager()
        tk.Label(master, text=f"Sistema de Archivos FAT ({rol})", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(master, text=f"Permisos: {', '.join(self.acciones)}", font=("Arial", 10)).pack(pady=3)
        self.lista = tk.Listbox(master, width=70, height=12)
        self.lista.pack(pady=10)
        frame_botones = tk.Frame(master)
        frame_botones.pack(pady=10)
        self.btn_crear = tk.Button(frame_botones, text="Crear archivo", command=self.ventana_crear)
        self.btn_crear.grid(row=0, column=0, padx=5)
        self.btn_abrir = tk.Button(frame_botones, text="Abrir archivo", command=self.abrir_archivo)
        self.btn_abrir.grid(row=0, column=1, padx=5)
        self.btn_modificar = tk.Button(frame_botones, text="Modificar archivo", command=self.ventana_modificar)
        self.btn_modificar.grid(row=0, column=2, padx=5)
        self.btn_eliminar = tk.Button(frame_botones, text="Eliminar archivo", command=self.eliminar_archivo)
        self.btn_eliminar.grid(row=0, column=3, padx=5)
        self.btn_actualizar = tk.Button(frame_botones, text="Actualizar lista", command=self.actualizar_lista)
        self.btn_actualizar.grid(row=0, column=4, padx=5)
        self.btn_ver_papelera = tk.Button(frame_botones, text="Ver papelera", command=self.ver_papelera)
        self.btn_ver_papelera.grid(row=0, column=5, padx=5)
        self.btn_asignar = tk.Button(frame_botones, text="Asignar permisos", command=self.ventana_asignar)
        self.btn_asignar.grid(row=0, column=6, padx=5)
        self.actualizar_botones()
        self.actualizar_lista()

    def actualizar_botones(self):
        self.btn_crear.config(state="normal" if ("crear" in self.acciones or "escribir" in self.acciones) else "disabled")
        self.btn_abrir.config(state="normal" if "leer" in self.acciones else "disabled")
        self.btn_eliminar.config(state="normal" if "eliminar" in self.acciones else "disabled")
        self.btn_modificar.config(state="normal" if "escribir" in self.acciones else "disabled")
        self.btn_asignar.config(state="normal" if "asignar" in self.acciones else "disabled")

    def actualizar_lista(self):
        self.lista.delete(0, tk.END)
        archivos = self.fat.listar_archivos()
        for a in archivos:
            self.lista.insert(tk.END, a)

    def ventana_crear(self):
        if "crear" not in self.acciones and "escribir" not in self.acciones:
            messagebox.showerror("Permiso denegado", "No tienes permiso para crear archivos.")
            return
        top = tk.Toplevel(self.master)
        top.title("Crear archivo")
        top.geometry("450x380")
        tk.Label(top, text="Nombre del archivo:").pack(pady=5)
        nombre_entry = tk.Entry(top)
        nombre_entry.pack()
        tk.Label(top, text="Contenido:").pack(pady=5)
        contenido_text = tk.Text(top, height=10, width=50)
        contenido_text.pack()
        def guardar():
            nombre = nombre_entry.get().strip()
            contenido = contenido_text.get("1.0", tk.END).strip()
            if not nombre:
                messagebox.showerror("Error", "Ingresa un nombre válido.")
                return
            try:
                self.fat.crear_archivo(nombre, contenido, self.rol, [])
                messagebox.showinfo("Éxito", f"Archivo '{nombre}' creado correctamente.")
                top.destroy()
                self.actualizar_lista()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        tk.Button(top, text="Guardar", command=guardar).pack(pady=10)

    def abrir_archivo(self):
        if "leer" not in self.acciones:
            messagebox.showerror("Permiso denegado", "No tienes permiso para leer archivos.")
            return
        seleccionado = self.lista.get(tk.ACTIVE)
        if not seleccionado:
            messagebox.showerror("Error", "Selecciona un archivo para abrir.")
            return
        try:
            contenido = self.fat.leer_archivo(seleccionado, self.rol)
            meta = self.fat.obtener_metadatos(seleccionado)
        except (PermissionError, FileNotFoundError) as e:
            messagebox.showerror("Error", str(e))
            return
        ventana = tk.Toplevel()
        ventana.title(f"Contenido - {seleccionado}")
        ventana.geometry("600x450")
        texto = tk.Text(ventana, wrap="word")
        texto.insert("1.0", contenido)
        texto.configure(state="disabled")
        texto.pack(expand=True, fill="both", padx=10, pady=10)
        info = (
            f"Nombre: {meta['nombre']}\n"
            f"Tamaño: {meta['tamaño']} bytes\n"
            f"Owner: {meta['owner']}\n"
            f"Creado: {meta['fecha_creacion']}\n"
            f"Ult. Modif.: {meta['fecha_modificacion']}\n"
            f"Permisos: {meta['permisos']}\n"
        )
        tk.Label(ventana, text=info, justify="left").pack(padx=10, pady=5)

    def ventana_modificar(self):
        if "escribir" not in self.acciones:
            messagebox.showerror("Permiso denegado", "No tienes permiso para modificar archivos.")
            return
        seleccionado = self.lista.get(tk.ACTIVE)
        if not seleccionado:
            messagebox.showerror("Error", "Selecciona un archivo para modificar.")
            return
        try:
            contenido_actual = self.fat.leer_archivo(seleccionado, self.rol)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        top = tk.Toplevel(self.master)
        top.title(f"Modificar - {seleccionado}")
        top.geometry("520x420")
        tk.Label(top, text=f"Modificando: {seleccionado}", font=("Arial", 12, "bold")).pack(pady=6)
        texto = tk.Text(top, height=18, width=60)
        texto.insert("1.0", contenido_actual)
        texto.pack(padx=10, pady=6)
        def guardar_modificacion():
            nuevo_contenido = texto.get("1.0", tk.END).rstrip("\n")
            try:
                self.fat.modificar_archivo(seleccionado, nuevo_contenido, self.rol)
                messagebox.showinfo("Éxito", "Archivo modificado correctamente.")
                top.destroy()
                self.actualizar_lista()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        tk.Button(top, text="Guardar cambios", command=guardar_modificacion).pack(pady=8)

    def eliminar_archivo(self):
        if "eliminar" not in self.acciones:
            messagebox.showerror("Permiso denegado", "No tienes permiso para eliminar archivos.")
            return
        seleccionado = self.lista.get(tk.ACTIVE)
        if not seleccionado:
            messagebox.showerror("Error", "Selecciona un archivo para eliminar.")
            return
        confirm = messagebox.askyesno("Confirmar", f"¿Mover '{seleccionado}' a papelera?")
        if confirm:
            try:
                self.fat.eliminar_archivo(seleccionado)
                messagebox.showinfo("Éxito", f"Archivo '{seleccionado}' movido a papelera.")
                self.actualizar_lista()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def ver_papelera(self):
        top = tk.Toplevel(self.master)
        top.title("Papelera de reciclaje")
        top.geometry("700x450")
        tk.Label(top, text="Archivos en papelera", font=("Arial", 12, "bold")).pack(pady=8)
        lista_papelera = tk.Listbox(top, width=100, height=15)
        lista_papelera.pack(pady=10)
        archivos_papelera = self.fat.obtener_datos_papelera()
        if not archivos_papelera:
            lista_papelera.insert(tk.END, "No hay archivos en la papelera.")
        else:
            for archivo in archivos_papelera:
                info = (
                    f"Nombre: {archivo['nombre']} | "
                    f"Tamaño: {archivo['tamaño']} bytes | "
                    f"Fecha eliminación: {archivo['fecha_eliminacion']} | "
                    f"Owner: {archivo.get('owner')}"
                )
                lista_papelera.insert(tk.END, info)
        def recuperar_sel():
            sel = lista_papelera.curselection()
            if not sel:
                messagebox.showerror("Error", "Selecciona un archivo para recuperar.")
                return
            linea = lista_papelera.get(sel[0])
            nombre = linea.split("|")[0].replace("Nombre:", "").strip()
            meta = self.fat.obtener_metadatos(nombre)
            if meta is None:
                messagebox.showerror("Error", "No se encontró el archivo.")
                return
            if meta.get("owner") != self.rol and "eliminar" not in self.acciones:
                messagebox.showerror("Permiso denegado", "No tienes permiso para recuperar este archivo.")
                return
            self.fat.recuperar_archivo(nombre)
            messagebox.showinfo("Éxito", f"Archivo '{nombre}' recuperado.")
            top.destroy()
            self.actualizar_lista()
        tk.Button(top, text="Recuperar seleccionado", command=recuperar_sel).pack(pady=6)

    def ventana_asignar(self):
        seleccionado = self.lista.get(tk.ACTIVE)
        if not seleccionado:
            messagebox.showerror("Error", "Selecciona un archivo para asignar permisos.")
            return
        meta = self.fat.obtener_metadatos(seleccionado)
        if not meta:
            messagebox.showerror("Error", "No se encontró el archivo.")
            return
        if meta.get("owner") != self.rol:
            messagebox.showerror("Permiso denegado", "Solo el owner puede asignar permisos.")
            return
        top = tk.Toplevel(self.master)
        top.title(f"Asignar permisos - {seleccionado}")
        top.geometry("400x300")
        tk.Label(top, text="Rol al que asignar permisos:").pack(pady=6)
        roles = list(self.permisos_globales.keys())
        combo_rol = ttk.Combobox(top, values=roles, state="readonly")
        combo_rol.pack(pady=6)
        combo_rol.current(0)
        var_leer = tk.BooleanVar()
        var_escribir = tk.BooleanVar()
        tk.Checkbutton(top, text="Leer", variable=var_leer).pack()
        tk.Checkbutton(top, text="Escribir", variable=var_escribir).pack()
        def aplicar():
            rol_obj = combo_rol.get()
            permisos_nuevos = []
            if var_leer.get():
                permisos_nuevos.append("leer")
            if var_escribir.get():
                permisos_nuevos.append("escribir")
            ok, msg = self.fat.asignar_permisos(seleccionado, self.rol, rol_obj, permisos_nuevos)
            if ok:
                messagebox.showinfo("Éxito", msg)
                top.destroy()
            else:
                messagebox.showerror("Error", msg)
        tk.Button(top, text="Aplicar permisos", command=aplicar).pack(pady=12)

if __name__ == "__main__":
    login = tk.Tk()
    app = LoginWindow(login)
    login.mainloop()
