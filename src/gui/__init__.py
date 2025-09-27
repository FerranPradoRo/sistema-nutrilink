"""
GUI de NutriLink
Login -> Menú -> Pacientes (CRUD + búsqueda + exportar PDF).
Carga el tema QSS y usa config.settings.
"""
from __future__ import annotations
import os, sys
from typing import List, Tuple, Optional

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication, QStyleFactory,
    QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QTableView, QToolBar,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QSpinBox, QComboBox,
    QFileDialog, QGroupBox, QFrame, QGraphicsDropShadowEffect,
)

from config import settings
from src.database.schema import init_schema
from src.auth import login as auth_login, register as auth_register
from src.database import list_patients, create_patient, update_patient, delete_patient

# =================== Helpers de estilo (QSS + “cards”) ===================

def load_qss(path: str) -> None:
    """Carga un archivo QSS en la aplicación (si existe)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            QApplication.instance().setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"[theme] No se encontró QSS: {path}")

def make_card(inner_layout) -> QFrame:
    """Envuelve un layout en un QFrame con sombra suave."""
    frame = QFrame()
    frame.setObjectName("Card")
    frame.setLayout(inner_layout)
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(30)
    shadow.setOffset(0, 8)
    shadow.setColor(QColor(2, 6, 23, 40))
    frame.setGraphicsEffect(shadow)
    return frame

# ============================ Tabla Pacientes ============================

HEADERS = [
    "ID","Nombre","Apellidos","Sexo","Edad",
    "Peso (kg)","Altura (cm)","Teléfono","Correo",
    "IMC","TMB","%Grasa","Peso Ideal",
]

class PatientsModel(QAbstractTableModel):
    def __init__(self, rows: List[Tuple]):
        super().__init__(); self.rows = rows
    def rowCount(self, _=QModelIndex()): return len(self.rows)
    def columnCount(self, _=QModelIndex()): return len(HEADERS)
    def headerData(self, sec, ori, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and ori == Qt.Orientation.Horizontal:
            return HEADERS[sec]
    def data(self, idx: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not idx.isValid(): return None
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self.rows[idx.row()][idx.column()])
    def get_row(self, r: int) -> Tuple: return self.rows[r]
    def update(self, rows: List[Tuple]):
        self.beginResetModel(); self.rows = rows; self.endResetModel()

# =============================== Diálogos ===============================

class PatientDialog(QDialog):
    """Crear/editar paciente (validación básica en GUI)."""
    def __init__(self, parent=None, data: Optional[Tuple]=None):
        super().__init__(parent); self.setWindowTitle("Paciente")
        form = QFormLayout(); form.setContentsMargins(28,28,28,28); form.setSpacing(12)
        h1 = QLabel("Paciente"); h1.setObjectName("H1"); form.addRow(h1)

        self.first = QLineEdit(); self.first.setPlaceholderText("Nombre(s)")
        self.last  = QLineEdit(); self.last.setPlaceholderText("Apellidos")
        self.sex   = QComboBox(); self.sex.addItems(["M","F"])
        self.age   = QSpinBox(); self.age.setRange(0,120)
        self.weight= QDoubleSpinBox(); self.weight.setRange(1,500); self.weight.setDecimals(2)
        self.height= QDoubleSpinBox(); self.height.setRange(30,250); self.height.setDecimals(1)
        self.phone = QLineEdit(); self.phone.setPlaceholderText("10 dígitos")
        self.email = QLineEdit(); self.email.setPlaceholderText("correo@dominio.com")
        for w in (self.first, self.last, self.phone, self.email): w.setClearButtonEnabled(True)

        form.addRow("Nombre*", self.first)
        form.addRow("Apellidos*", self.last)
        form.addRow("Sexo*", self.sex)
        form.addRow("Edad*", self.age)
        form.addRow("Peso (kg)*", self.weight)
        form.addRow("Altura (cm)*", self.height)
        form.addRow("Teléfono", self.phone)
        form.addRow("Correo", self.email)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.button(QDialogButtonBox.StandardButton.Ok).setProperty("type","primary")
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        form.addRow(bb)

        if data:
            self.first.setText(data[1]); self.last.setText(data[2]); self.sex.setCurrentText(data[3])
            self.age.setValue(int(data[4])); self.weight.setValue(float(data[5])); self.height.setValue(float(data[6]))
            self.phone.setText(data[7] or ""); self.email.setText(data[8] or "")

        outer = QVBoxLayout(self); outer.setContentsMargins(12,12,12,12)
        outer.addWidget(make_card(form))

    def values(self) -> Optional[dict]:
        if not self.first.text().strip() or not self.last.text().strip():
            QMessageBox.warning(self,"Validación","Nombre y apellidos son obligatorios")
            return None
        return {
            "first_name": self.first.text().strip(),
            "last_name":  self.last.text().strip(),
            "sex":        self.sex.currentText(),
            "age":        int(self.age.value()),
            "weight_kg":  float(self.weight.value()),
            "height_cm":  float(self.height.value()),
            "phone":      self.phone.text().strip() or None,
            "email":      self.email.text().strip() or None,
        }

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Crear cuenta")

        form = QFormLayout(); form.setContentsMargins(28,28,28,28); form.setSpacing(12)

        # Cabecera con hoja + título
        header = QVBoxLayout()
        leaf = QLabel("🌿"); leaf.setObjectName("LogoEmoji")
        leaf.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        leaf.setStyleSheet("font-size: 72px; line-height: 1;")
        h1 = QLabel("Crear cuenta"); h1.setObjectName("H1"); h1.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        header.addWidget(leaf); header.addWidget(h1)
        form.addRow(header)

        self.name  = QLineEdit(); self.name.setPlaceholderText("Tu nombre completo")
        self.email = QLineEdit(); self.email.setPlaceholderText("tu.correo@ejemplo.com")
        self.p1    = QLineEdit(); self.p1.setEchoMode(QLineEdit.EchoMode.Password); self.p1.setPlaceholderText("Crea una contraseña segura")
        self.p2    = QLineEdit(); self.p2.setEchoMode(QLineEdit.EchoMode.Password); self.p2.setPlaceholderText("Confirma tu contraseña")
        for w in (self.name, self.email, self.p1, self.p2): w.setClearButtonEnabled(True)

        form.addRow("Nombre*", self.name)
        form.addRow("Correo*", self.email)
        form.addRow("Contraseña*", self.p1)
        form.addRow("Confirmar*", self.p2)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.button(QDialogButtonBox.StandardButton.Ok).setText("Registrarme")
        bb.button(QDialogButtonBox.StandardButton.Ok).setProperty("type","primary")
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        form.addRow(bb)

        outer = QVBoxLayout(self); outer.setContentsMargins(12,12,12,12)
        card = make_card(form)
        card.setFixedWidth(480)
        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)

    def values(self):
        if not self.name.text().strip() or not self.email.text().strip() or not self.p1.text():
            QMessageBox.warning(self,"Validación","Completa todos los campos."); return None
        if self.p1.text() != self.p2.text():
            QMessageBox.warning(self,"Validación","Las contraseñas no coinciden."); return None
        return {"name": self.name.text().strip(), "email": self.email.text().strip(), "password": self.p1.text()}

# ================================ Páginas ================================

class LoginPage(QWidget):
    def __init__(self, on_success):
        super().__init__(); self.on_success = on_success
        root = QVBoxLayout(self); root.setContentsMargins(40,40,40,40)
        root.addStretch(1)

        # --- Logo (hoja grande + texto) ---
        logo_wrap = QVBoxLayout()
        leaf = QLabel("🌿")
        leaf.setObjectName("LogoEmoji")
        leaf.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        leaf.setStyleSheet("font-size: 88px; line-height: 1;")  # tamaño del icono
        title = QLabel("NutriLink"); title.setObjectName("AppLogoText")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        logo_wrap.addWidget(leaf); logo_wrap.addWidget(title)

        # --- Formulario en Card ---
        form = QFormLayout(); form.setContentsMargins(28,28,28,28); form.setSpacing(12)
        h1 = QLabel("Iniciar sesión"); h1.setObjectName("H1"); form.addRow(h1)

        self.email = QLineEdit(); self.email.setPlaceholderText("Correo electrónico"); self.email.setClearButtonEnabled(True)
        self.pwd   = QLineEdit(); self.pwd.setEchoMode(QLineEdit.EchoMode.Password); self.pwd.setPlaceholderText("Contraseña"); self.pwd.setClearButtonEnabled(True)
        form.addRow(" ", self.email)
        form.addRow(" ", self.pwd)

        btns = QHBoxLayout()
        b_login = QPushButton("Entrar"); b_login.setProperty("type","primary")
        b_reg   = QPushButton("Crear cuenta…")
        btns.addWidget(b_login); btns.addWidget(b_reg)
        form.addRow(btns)

        card = make_card(form)
        card.setFixedWidth(440)  # ancho del cuadro de login

        root.addLayout(logo_wrap)
        root.addSpacing(12)
        root.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addStretch(2)

        b_login.clicked.connect(self._try_login)
        b_reg.clicked.connect(self._register)

    def _try_login(self):
        res = auth_login(self.email.text().strip(), self.pwd.text())
        if not res:
            QMessageBox.warning(self,"Error","Credenciales inválidas o bloque demasiado reciente.")
            return
        self.on_success(*res)  # (id_user, name)

    def _register(self):
        dlg = RegisterDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            vals = dlg.values()
            if not vals: return
            try:
                auth_register(vals["name"], vals["email"], vals["password"])
                QMessageBox.information(self,"Listo","Cuenta creada. Ahora inicia sesión.")
            except Exception as e:
                QMessageBox.critical(self,"Registro", str(e))

class MainMenu(QWidget):
    def __init__(self, user_id: int, user_name: str, go_patients, do_logout):
        super().__init__()
        lay = QVBoxLayout(self)
        hdr = QLabel(f"¡Hola, {user_name}!")
        hdr.setStyleSheet("font-size:20px; font-weight:bold;")
        lay.addWidget(hdr)

        box = QGroupBox("Menú principal")
        hb = QHBoxLayout(box)
        btn_pat = QPushButton("Pacientes"); btn_pat.setProperty("type","primary")
        btn_logout = QPushButton("Cerrar sesión")
        hb.addWidget(btn_pat); hb.addWidget(btn_logout)
        lay.addWidget(box); lay.addStretch()

        btn_pat.clicked.connect(lambda: go_patients(user_id))
        btn_logout.clicked.connect(do_logout)

class PatientsPage(QWidget):
    def __init__(self, id_user: int):
        super().__init__(); self.id_user = id_user
        lay = QVBoxLayout(self)
        tb = QToolBar(); lay.addWidget(tb)

        self.search = QLineEdit(); self.search.setPlaceholderText("Buscar nombre/apellidos…")
        bsearch = QPushButton("Buscar");  bsearch.setProperty("type","primary")
        bclear  = QPushButton("Limpiar")
        badd    = QPushButton("Agregar");  badd.setProperty("type","success")
        bedit   = QPushButton("Editar");   bedit.setProperty("type","warn")
        bdel    = QPushButton("Eliminar"); bdel.setProperty("type","danger")
        bexport = QPushButton("Exportar a PDF"); bexport.setProperty("type","primary")
        for w in (self.search, bsearch, bclear, badd, bedit, bdel, bexport): tb.addWidget(w)

        self.table = QTableView(); self.table.setAlternatingRowColors(True)
        table_wrap = QVBoxLayout(); table_wrap.setContentsMargins(12,12,12,12); table_wrap.addWidget(self.table)
        lay.addWidget(make_card(table_wrap))

        bsearch.clicked.connect(lambda: self.refresh(self.search.text().strip()))
        bclear.clicked.connect(lambda: (self.search.clear(), self.refresh("")))
        badd.clicked.connect(self._add); bedit.clicked.connect(self._edit)
        bdel.clicked.connect(self._delete); bexport.clicked.connect(self._export)

        self.refresh()

    def refresh(self, q: str = ""):
        rows = list_patients(self.id_user, q)
        if not hasattr(self, "model"):
            self.model = PatientsModel(rows); self.table.setModel(self.model)
        else:
            self.model.update(rows)
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> Optional[int]:
        idx = self.table.currentIndex()
        if not idx.isValid(): return None
        return int(self.model.get_row(idx.row())[0])

    def _add(self):
        dlg = PatientDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            vals = dlg.values()
            if not vals: return
            try:
                create_patient(self.id_user, **vals); self.refresh(self.search.text().strip())
            except Exception as e:
                QMessageBox.critical(self,"Error", str(e))

    def _edit(self):
        pid = self._selected_id()
        if pid is None:
            QMessageBox.information(self,"Editar","Selecciona un paciente"); return
        current = next((r for r in self.model.rows if r[0] == pid), None)
        dlg = PatientDialog(self, current)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            vals = dlg.values()
            if not vals: return
            try:
                update_patient(pid, **vals); self.refresh(self.search.text().strip())
            except Exception as e:
                QMessageBox.critical(self,"Error", str(e))

    def _delete(self):
        pid = self._selected_id()
        if pid is None:
            QMessageBox.information(self,"Eliminar","Selecciona un paciente"); return
        if QMessageBox.question(self,"Confirmar","¿Eliminar paciente seleccionado?") == QMessageBox.StandardButton.Yes:
            delete_patient(pid); self.refresh(self.search.text().strip())

    def _export(self):
        default_path = (settings.PDF_EXPORT_DIR / "pacientes.pdf").as_posix()
        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", default_path, "PDF (*.pdf)")
        if not path: return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            from src.reports import export_patients_pdf
            export_patients_pdf(self.model.rows, path)
            QMessageBox.information(self,"PDF","Exportado correctamente.")
        except Exception as e:
            QMessageBox.warning(self,"PDF", str(e))

# ============================ Bootstrap App ============================

def main():
    # Un solo QApplication aquí
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setApplicationName(settings.APP_NAME)
    app.setApplicationVersion(settings.APP_VERSION)

    # init BD
    init_schema()

    # Stack de navegación
    stack = QStackedWidget()

    def to_login():
        page = LoginPage(on_success=on_login)
        stack.addWidget(page)
        stack.setCurrentWidget(page)

    def on_login(user_id: int, user_name: str):
        menu = MainMenu(user_id, user_name, go_patients=lambda uid: to_patients(uid), do_logout=to_login)
        stack.addWidget(menu)
        stack.setCurrentWidget(menu)

    def to_patients(uid: int):
        page = PatientsPage(uid)
        stack.addWidget(page)
        stack.setCurrentWidget(page)

    # Cargar QSS
    theme_path = (settings.BASE_DIR / "config" / "theme.qss").as_posix()
    load_qss(theme_path)

    # Tamaños de ventana desde settings
    stack.setMinimumSize(settings.WINDOW_MIN_WIDTH, settings.WINDOW_MIN_HEIGHT)
    stack.resize(settings.WINDOW_DEFAULT_WIDTH, settings.WINDOW_DEFAULT_HEIGHT)

    # Lanzar
    to_login()
    stack.show()
    return app.exec()