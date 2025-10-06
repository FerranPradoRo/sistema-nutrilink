"""
NutriLink - GUI completa (PyQt6)
- Login (email/contraseña) con Ver/Ocultar
- Menú principal centrado + imagen redonda responsiva
- Pacientes: CRUD + búsqueda + exportación PDF horizontal
- Cerrar sesión
"""

from __future__ import annotations
import os
import sys
from typing import List, Tuple, Optional

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor, QPixmap, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QApplication, QStyleFactory,
    QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QTableView, QToolBar,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QSpinBox, QComboBox,
    QFileDialog, QGroupBox, QFrame, QGraphicsDropShadowEffect
)

# ========================= Integración con tu proyecto =========================
from config import settings
from src.database.schema import init_schema
from src.auth import login as auth_login, register as auth_register
from src.database import list_patients, create_patient, update_patient, delete_patient
# export_patients_pdf(rows, path) debe generar PDF en horizontal
from src.reports import export_patients_pdf

# ============================ Utilidades de estilo =============================

def load_qss(path: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            QApplication.instance().setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"[theme] No se encontró QSS: {path}")

def top_accent(height: int = 14) -> QFrame:
    bar = QFrame(); bar.setObjectName("TopAccent"); bar.setFixedHeight(height); return bar

def make_card(inner_layout) -> QFrame:
    frame = QFrame(); frame.setObjectName("Card"); frame.setLayout(inner_layout)
    shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(28); shadow.setOffset(0,8)
    shadow.setColor(QColor(2,6,23,40)); frame.setGraphicsEffect(shadow)
    return frame

# --------- Campo de contraseña con botón Ver/Ocultar SIEMPRE visible ----------
def make_password_field(placeholder: str = "Contraseña") -> tuple[QWidget, QLineEdit]:
    """
    Devuelve (contenedor, line_edit): botón [Ver]/[Ocultar] a la derecha.
    No usa emojis ni íconos PNG, para máxima visibilidad en cualquier tema.
    """
    wrap = QWidget(); lay = QHBoxLayout(wrap)
    lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)

    edit = QLineEdit(); edit.setPlaceholderText(placeholder)
    edit.setEchoMode(QLineEdit.EchoMode.Password); edit.setClearButtonEnabled(True)

    btn = QPushButton("Ver"); btn.setObjectName("EyeChip")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setCheckable(True); btn.setMinimumHeight(28); btn.setMaximumWidth(88)

    def toggle(checked: bool):
        if checked:
            edit.setEchoMode(QLineEdit.EchoMode.Normal); btn.setText("Ocultar")
        else:
            edit.setEchoMode(QLineEdit.EchoMode.Password); btn.setText("Ver")
    btn.toggled.connect(toggle)

    lay.addWidget(edit, 1); lay.addWidget(btn, 0, Qt.AlignmentFlag.AlignRight)
    return wrap, edit

# ------------------------ Imagen héroe (circular responsiva) ------------------

def find_hero_image() -> Optional[QPixmap]:
    names = ["nutrilink.png", "hero.png", "NutriLink.png", "nl.png"]
    for n in names:
        p = (settings.BASE_DIR / n)
        if p.exists():
            px = QPixmap(p.as_posix())
            if not px.isNull():
                return px
    return None

def make_round_pixmap(src: QPixmap, diameter: int) -> QPixmap:
    out = QPixmap(diameter, diameter); out.fill(Qt.GlobalColor.transparent)
    painter = QPainter(out); painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath(); path.addEllipse(0,0,diameter,diameter); painter.setClipPath(path)
    scaled = src.scaled(diameter, diameter, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation)
    x = (scaled.width() - diameter)//2; y=(scaled.height() - diameter)//2
    painter.drawPixmap(-x, -y, scaled); painter.end(); return out

# ============================== Tabla de pacientes =============================

HEADERS = ["#","Nombre","Apellidos","Sexo","Edad","Peso (kg)","Altura (cm)","Teléfono","Correo","IMC","TMB","%Grasa","Peso Ideal"]

class PatientsModel(QAbstractTableModel):
    def __init__(self, rows: List[Tuple]): super().__init__(); self.rows = rows
    def rowCount(self, _=QModelIndex()): return len(self.rows)
    def columnCount(self, _=QModelIndex()): return len(HEADERS)
    def headerData(self, sec, ori, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and ori == Qt.Orientation.Horizontal: return HEADERS[sec]
    def data(self, idx: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not idx.isValid(): return None
        if role == Qt.ItemDataRole.DisplayRole:
            r = self.rows[idx.row()]
            if idx.column() == 0: return str(idx.row()+1)  # Folio visual (no el ID real)
            return "" if r[idx.column()] is None else str(r[idx.column()])
    def get_row(self, r: int) -> Tuple: return self.rows[r]
    def update(self, rows: List[Tuple]): self.beginResetModel(); self.rows = rows; self.endResetModel()

# ================================== Diálogos ==================================

class PatientDialog(QDialog):
    def __init__(self, parent=None, data: Optional[Tuple]=None):
        super().__init__(parent); self.setWindowTitle("Paciente")
        form = QFormLayout(); form.setContentsMargins(28,28,28,28); form.setSpacing(12)
        h1 = QLabel("Paciente"); h1.setObjectName("H1"); form.addRow(h1)

        self.first = QLineEdit(); self.last = QLineEdit()
        self.sex = QComboBox(); self.sex.addItems(["M","F"])
        self.age = QSpinBox(); self.age.setRange(0,120)
        self.weight= QDoubleSpinBox(); self.weight.setRange(1,500); self.weight.setDecimals(2)
        self.height= QDoubleSpinBox(); self.height.setRange(30,250); self.height.setDecimals(1)
        self.phone = QLineEdit(); self.email = QLineEdit()
        self.first.setPlaceholderText("Nombre(s)"); self.last.setPlaceholderText("Apellidos")
        self.phone.setPlaceholderText("10 dígitos"); self.email.setPlaceholderText("correo@dominio.com")
        for w in (self.first,self.last,self.phone,self.email): w.setClearButtonEnabled(True)

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

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Crear cuenta")
        form = QFormLayout(); form.setContentsMargins(28,28,28,28); form.setSpacing(12)

        header = QVBoxLayout()
        banner = QLabel(); banner.setFixedHeight(80); banner.setStyleSheet("background:#eef3fb;border-radius:12px;")
        leaf = QLabel("🌿"); leaf.setAlignment(Qt.AlignmentFlag.AlignHCenter); leaf.setStyleSheet("font-size:42px;")
        bl = QVBoxLayout(banner); bl.addWidget(leaf, 0, Qt.AlignmentFlag.AlignCenter)
        h1 = QLabel("Crear cuenta"); h1.setObjectName("H1"); h1.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        header.addWidget(banner); header.addWidget(h1)
        form.addRow(header)

        self.name = QLineEdit(); self.name.setPlaceholderText("Tu nombre completo")
        self.email= QLineEdit(); self.email.setPlaceholderText("tu.correo@ejemplo.com")
        pwrap1, self.p1 = make_password_field("Crea una contraseña segura")
        pwrap2, self.p2 = make_password_field("Confirma tu contraseña")
        for w in (self.name, self.email): w.setClearButtonEnabled(True)

        form.addRow("Nombre*", self.name)
        form.addRow("Correo*", self.email)
        form.addRow("Contraseña*", pwrap1)
        form.addRow("Confirmar*", pwrap2)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.button(QDialogButtonBox.StandardButton.Ok).setText("Registrarme")
        bb.button(QDialogButtonBox.StandardButton.Ok).setProperty("type","primary")
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        form.addRow(bb)

        outer = QVBoxLayout(self); outer.setContentsMargins(12,12,12,12)
        card = make_card(form); card.setFixedWidth(520)
        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)

# =================================== Páginas ===================================

class LoginPage(QWidget):
    def __init__(self, on_success, on_forgot):
        super().__init__(); self.on_success = on_success; self.on_forgot = on_forgot
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0)
        root.addWidget(top_accent(), 0)

        inner = QVBoxLayout(); inner.setContentsMargins(40,40,40,40)
        inner.addStretch(1)

        logo_wrap = QVBoxLayout()
        leaf = QLabel("🌿"); leaf.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        leaf.setStyleSheet("font-size:88px;line-height:1;")
        title = QLabel("NutriLink"); title.setObjectName("AppLogoText"); title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        logo_wrap.addWidget(leaf); logo_wrap.addWidget(title)

        form = QFormLayout(); form.setContentsMargins(28,28,28,28); form.setSpacing(12)
        h1 = QLabel("Iniciar sesión"); h1.setObjectName("H1"); form.addRow(h1)

        self.email = QLineEdit(); self.email.setPlaceholderText("Correo electrónico"); self.email.setClearButtonEnabled(True)
        pwrap, self.pwd = make_password_field("Contraseña")

        form.addRow(" ", self.email)
        form.addRow(" ", pwrap)

        btns = QHBoxLayout()
        b_login = QPushButton("Entrar"); b_login.setProperty("type","primary")
        b_reg   = QPushButton("Crear cuenta…")
        btns.addWidget(b_login); btns.addWidget(b_reg)
        form.addRow(btns)

        link = QPushButton("¿Olvidaste tu contraseña?")
        link.setFlat(True); link.clicked.connect(self._forgot)
        form.addRow(link)

        card = make_card(form); card.setFixedWidth(460)
        inner.addLayout(logo_wrap); inner.addSpacing(12)
        inner.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        inner.addStretch(2)

        root.addLayout(inner)

        b_login.clicked.connect(self._try_login)
        b_reg.clicked.connect(self._register)

    def _try_login(self):
        email = self.email.text().strip(); pwd = self.pwd.text()
        res = auth_login(email, pwd)
        if not res:
            QMessageBox.warning(self, "Error", "Credenciales inválidas o bloqueo temporal.")
            return
        self.on_success(*res)

    def _register(self):
        dlg = RegisterDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.name.text().strip(); email = dlg.email.text().strip()
            p1 = dlg.p1.text(); p2 = dlg.p2.text()
            if not name or not email or not p1:
                QMessageBox.warning(self,"Registro","Completa todos los campos obligatorios."); return
            if p1 != p2:
                QMessageBox.warning(self,"Registro","Las contraseñas no coinciden."); return
            try:
                auth_register(name, email, p1)
                QMessageBox.information(self,"Listo","Cuenta creada. Ahora inicia sesión.")
            except Exception as e:
                QMessageBox.critical(self,"Registro", str(e))

    def _forgot(self):
        QMessageBox.information(self, "Recuperación", "Función de email desactivada por ahora.")

class MainMenu(QWidget):
    """
    Menú principal sin imagen: encabezado con 🌿 centrado + saludo y botones
    centrados como el login.
    """
    def __init__(self, user_id: int, user_name: str, go_patients, do_logout):
        super().__init__()
        self._go_patients = go_patients
        self._do_logout = do_logout
        self._user_id = user_id

        # Layout raíz
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(top_accent(), 0)

        # Cuerpo centrado (como login)
        body = QVBoxLayout()
        body.setContentsMargins(40, 40, 40, 40)
        body.setSpacing(16)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo/hoja
        leaf = QLabel("🌿")
        leaf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        leaf.setStyleSheet("font-size: 88px; line-height: 1;")

        # Títulos
        hello = QLabel(f"¡Hola, {user_name}!")
        hello.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hello.setStyleSheet("font-size: 34px; font-weight: 900; letter-spacing: .2px;")

        title = QLabel("Menú Principal")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #111;")

        # Card con botones (igual estilo que login)
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        btn_pat = QPushButton("Pacientes")
        btn_pat.setProperty("type", "primary")
        btn_pat.setFixedHeight(56)
        btn_pat.setStyleSheet("border-radius: 22px; font-weight: 600;")

        btn_logout = QPushButton("Cerrar sesión")
        btn_logout.setFixedHeight(56)
        btn_logout.setStyleSheet("border-radius: 22px; font-weight: 500;")

        card_layout.addWidget(btn_pat)
        card_layout.addWidget(btn_logout)

        card = make_card(card_layout)
        card.setFixedWidth(460)

        # Ensamble
        body.addWidget(leaf)
        body.addWidget(hello)
        body.addWidget(title)
        body.addSpacing(6)
        body.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)

        outer.addLayout(body)

        # Acciones
        btn_pat.clicked.connect(lambda: self._go_patients(self._user_id))
        btn_logout.clicked.connect(self._do_logout)
        
class PatientsPage(QWidget):
    def __init__(self, id_user: int, on_logout):
        super().__init__(); self.id_user = id_user; self.on_logout = on_logout
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        lay.addWidget(top_accent(), 0)

        inner = QVBoxLayout(); inner.setContentsMargins(16,16,16,16)

        tb = QToolBar(); inner.addWidget(tb)
        self.search = QLineEdit(); self.search.setPlaceholderText("Buscar nombre/apellidos…")
        bsearch = QPushButton("Buscar");  bsearch.setProperty("type","primary")
        bclear  = QPushButton("Limpiar")
        badd    = QPushButton("Agregar");  badd.setProperty("type","success")
        bedit   = QPushButton("Editar");   bedit.setProperty("type","warn")
        bdel    = QPushButton("Eliminar"); bdel.setProperty("type","danger")
        bexport = QPushButton("Exportar a PDF"); bexport.setProperty("type","primary")
        blogout = QPushButton("Cerrar sesión")
        for w in (self.search, bsearch, bclear, badd, bedit, bdel, bexport, blogout): tb.addWidget(w)

        self.table = QTableView(); self.table.setAlternatingRowColors(True)
        table_wrap = QVBoxLayout(); table_wrap.setContentsMargins(12,12,12,12); table_wrap.addWidget(self.table)
        inner.addWidget(make_card(table_wrap))
        lay.addLayout(inner)

        bsearch.clicked.connect(lambda: self.refresh(self.search.text().strip()))
        bclear.clicked.connect(lambda: (self.search.clear(), self.refresh("")))
        badd.clicked.connect(self._add); bedit.clicked.connect(self._edit)
        bdel.clicked.connect(self._delete); bexport.clicked.connect(self._export)
        blogout.clicked.connect(self.on_logout)

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
        return int(self.model.get_row(idx.row())[0])  # id real (col 0 en rows, no la visible)

    def _add(self):
        dlg = PatientDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            vals = {
                "first_name": dlg.first.text().strip(),
                "last_name": dlg.last.text().strip(),
                "sex": dlg.sex.currentText(),
                "age": int(dlg.age.value()),
                "weight_kg": float(dlg.weight.value()),
                "height_cm": float(dlg.height.value()),
                "phone": dlg.phone.text().strip() or None,
                "email": dlg.email.text().strip() or None,
            }
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
            vals = {
                "first_name": dlg.first.text().strip(),
                "last_name": dlg.last.text().strip(),
                "sex": dlg.sex.currentText(),
                "age": int(dlg.age.value()),
                "weight_kg": float(dlg.weight.value()),
                "height_cm": float(dlg.height.value()),
                "phone": dlg.phone.text().strip() or None,
                "email": dlg.email.text().strip() or None,
            }
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
            export_patients_pdf(self.model.rows, path)  # Debe escribir en formato horizontal
            QMessageBox.information(self,"PDF","Exportado correctamente (horizontal).")
        except Exception as e:
            QMessageBox.warning(self,"PDF", str(e))

# ================================ Bootstrap ====================================

def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setApplicationName(settings.APP_NAME)
    app.setApplicationVersion(settings.APP_VERSION)

    # Tema
    theme_path = (settings.BASE_DIR / "config" / "theme.qss").as_posix()
    load_qss(theme_path)

    # BD
    init_schema()

    # Navegación
    stack = QStackedWidget()

    def reset_to_login():
        while stack.count():
            w = stack.widget(0); stack.removeWidget(w); w.deleteLater()
        to_login()

    def to_login():
        page = LoginPage(on_success=on_login, on_forgot=lambda: None)
        stack.addWidget(page); stack.setCurrentWidget(page)

    def on_login(user_id: int, user_name: str):
        menu = MainMenu(user_id, user_name,
                        go_patients=lambda uid: to_patients(uid),
                        do_logout=reset_to_login)
        stack.addWidget(menu); stack.setCurrentWidget(menu)

    def to_patients(uid: int):
        page = PatientsPage(uid, on_logout=reset_to_login)
        stack.addWidget(page); stack.setCurrentWidget(page)

    stack.setMinimumSize(settings.WINDOW_MIN_WIDTH, settings.WINDOW_MIN_HEIGHT)
    stack.resize(settings.WINDOW_DEFAULT_WIDTH, settings.WINDOW_DEFAULT_HEIGHT)
    to_login()
    stack.show()
    return app.exec()