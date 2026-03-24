from __future__ import annotations
import sys
from typing import List, Tuple, Optional

from PyQt6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, QPropertyAnimation,
    QParallelAnimationGroup, QEasingCurve, QPoint, QDate, QTime
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication, QStyleFactory, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTableView, QToolBar,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QSpinBox, QComboBox, QFileDialog,
    QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QTextEdit,
    QDateEdit, QTimeEdit, QSizePolicy
)

from config import settings
from src.database.schema import init_schema
from src.auth import login as auth_login, register as auth_register, valid_email, valid_phone
from src.database import (
    list_patients, create_patient, update_patient, delete_patient,
    create_appointment, update_appointment, delete_appointment,
    list_upcoming_appointments, list_patients_basic, get_user_name
)
from src.reports import export_patients_pdf


# =========================================================
# HELPERS
# =========================================================

def load_qss(path: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            QApplication.instance().setStyleSheet(f.read())
    except FileNotFoundError:
        pass


def top_accent() -> QFrame:
    bar = QFrame()
    bar.setObjectName("TopAccent")
    return bar


def make_shadow(widget: QWidget, blur: int = 28, offset_y: int = 8, alpha: int = 40):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, offset_y)
    shadow.setColor(QColor(2, 6, 23, alpha))
    widget.setGraphicsEffect(shadow)


def make_card(inner_layout, object_name: str = "GlassCard") -> QFrame:
    frame = QFrame()
    frame.setObjectName(object_name)
    frame.setLayout(inner_layout)
    make_shadow(frame)
    return frame


def make_stat_card(title: str, value: str) -> QFrame:
    lay = QVBoxLayout()
    lay.setContentsMargins(18, 14, 18, 14)
    lay.setSpacing(4)

    t = QLabel(title)
    t.setObjectName("StatTitle")

    v = QLabel(value)
    v.setObjectName("StatValue")

    lay.addWidget(t)
    lay.addWidget(v)

    card = make_card(lay, "GlassCard")
    card.setMinimumWidth(138)
    card.setMaximumWidth(170)
    return card


def make_password_field(placeholder: str):
    wrap = QWidget()
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    edit = QLineEdit()
    edit.setPlaceholderText(placeholder)
    edit.setEchoMode(QLineEdit.EchoMode.Password)
    edit.setClearButtonEnabled(True)

    btn = QPushButton("Ver")
    btn.setObjectName("EyeChip")
    btn.setCheckable(True)

    def toggle(checked: bool):
        if checked:
            edit.setEchoMode(QLineEdit.EchoMode.Normal)
            btn.setText("Ocultar")
        else:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            btn.setText("Ver")

    btn.toggled.connect(toggle)

    lay.addWidget(edit, 1)
    lay.addWidget(btn, 0)
    return wrap, edit


def icon_button(text: str, kind: str | None = None) -> QPushButton:
    btn = QPushButton(text)
    if kind:
        btn.setProperty("type", kind)
    btn.setFixedHeight(44)
    return btn


# =========================================================
# MODELS
# =========================================================

PATIENT_HEADERS = [
    "#", "Nombre", "Apellidos", "Sexo", "Edad", "Peso", "Altura",
    "Teléfono", "Correo", "IMC", "TMB", "% Grasa", "Peso Ideal"
]

APPOINTMENT_HEADERS = ["#", "Paciente", "Fecha", "Hora", "Estado", "Notas"]


class PatientsModel(QAbstractTableModel):
    def __init__(self, rows: List[Tuple]):
        super().__init__()
        self.rows = rows

    def rowCount(self, _=QModelIndex()):
        return len(self.rows)

    def columnCount(self, _=QModelIndex()):
        return len(PATIENT_HEADERS)

    def headerData(self, sec, ori, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and ori == Qt.Orientation.Horizontal:
            return PATIENT_HEADERS[sec]

    def data(self, idx: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not idx.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            row = self.rows[idx.row()]
            if idx.column() == 0:
                return str(idx.row() + 1)
            return "" if row[idx.column()] is None else str(row[idx.column()])

    def get_row(self, r: int) -> Tuple:
        return self.rows[r]

    def update(self, rows: List[Tuple]):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()


class AppointmentsModel(QAbstractTableModel):
    def __init__(self, rows: List[Tuple]):
        super().__init__()
        self.rows = rows

    def rowCount(self, _=QModelIndex()):
        return len(self.rows)

    def columnCount(self, _=QModelIndex()):
        return len(APPOINTMENT_HEADERS)

    def headerData(self, sec, ori, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and ori == Qt.Orientation.Horizontal:
            return APPOINTMENT_HEADERS[sec]

    def data(self, idx: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not idx.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            row = self.rows[idx.row()]
            if idx.column() == 0:
                return str(idx.row() + 1)
            return "" if row[idx.column()] is None else str(row[idx.column()])

    def get_row(self, r: int) -> Tuple:
        return self.rows[r]

    def update(self, rows: List[Tuple]):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()


# =========================================================
# DIALOGS
# =========================================================

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear cuenta")

        form = QFormLayout()
        form.setContentsMargins(28, 28, 28, 28)
        form.setSpacing(14)

        title = QLabel("Crear cuenta")
        title.setObjectName("H1")
        form.addRow(title)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Nombre completo")

        self.email = QLineEdit()
        self.email.setPlaceholderText("correo@ejemplo.com")

        p1_wrap, self.p1 = make_password_field("Contraseña")
        p2_wrap, self.p2 = make_password_field("Confirmar contraseña")

        form.addRow("Nombre*", self.name)
        form.addRow("Correo*", self.email)
        form.addRow("Contraseña*", p1_wrap)
        form.addRow("Confirmar*", p2_wrap)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.button(QDialogButtonBox.StandardButton.Ok).setText("Registrarme")
        bb.button(QDialogButtonBox.StandardButton.Ok).setProperty("type", "primary")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)

        form.addRow(bb)

        outer = QVBoxLayout(self)
        outer.addWidget(make_card(form))


class PatientDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Paciente")

        form = QFormLayout()
        form.setContentsMargins(28, 28, 28, 28)
        form.setSpacing(12)

        title = QLabel("Paciente")
        title.setObjectName("H1")
        form.addRow(title)

        self.first = QLineEdit()
        self.last = QLineEdit()

        self.sex = QComboBox()
        self.sex.addItems(["M", "F"])

        self.age = QSpinBox()
        self.age.setRange(1, 120)

        self.weight = QDoubleSpinBox()
        self.weight.setRange(1, 300)
        self.weight.setDecimals(2)

        self.height = QDoubleSpinBox()
        self.height.setRange(50, 250)
        self.height.setDecimals(1)

        self.phone = QLineEdit()
        self.email = QLineEdit()

        self.first.setPlaceholderText("Nombre")
        self.last.setPlaceholderText("Apellidos")
        self.phone.setPlaceholderText("10 dígitos")
        self.email.setPlaceholderText("correo@ejemplo.com")

        form.addRow("Nombre*", self.first)
        form.addRow("Apellidos*", self.last)
        form.addRow("Sexo*", self.sex)
        form.addRow("Edad*", self.age)
        form.addRow("Peso (kg)*", self.weight)
        form.addRow("Altura (cm)*", self.height)
        form.addRow("Teléfono", self.phone)
        form.addRow("Correo", self.email)

        if data:
            self.first.setText(str(data[1]))
            self.last.setText(str(data[2]))
            self.sex.setCurrentText(str(data[3]))
            self.age.setValue(int(data[4]))
            self.weight.setValue(float(data[5]))
            self.height.setValue(float(data[6]))
            self.phone.setText("" if data[7] is None else str(data[7]))
            self.email.setText("" if data[8] is None else str(data[8]))

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.button(QDialogButtonBox.StandardButton.Ok).setProperty("type", "primary")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        form.addRow(bb)

        outer = QVBoxLayout(self)
        outer.addWidget(make_card(form))


class AppointmentDialog(QDialog):
    def __init__(self, id_user: int, parent=None):
        super().__init__(parent)
        self.id_user = id_user
        self.setWindowTitle("Nueva cita")

        form = QFormLayout()
        form.setContentsMargins(28, 28, 28, 28)
        form.setSpacing(12)

        title = QLabel("Registrar cita")
        title.setObjectName("H1")
        form.addRow(title)

        self.patient_combo = QComboBox()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())

        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Programada", "Atendida", "Cancelada"])

        self.notes = QTextEdit()
        self.notes.setFixedHeight(100)

        for pid, full_name in list_patients_basic(id_user):
            self.patient_combo.addItem(full_name, pid)

        form.addRow("Paciente*", self.patient_combo)
        form.addRow("Fecha*", self.date_edit)
        form.addRow("Hora*", self.time_edit)
        form.addRow("Estado*", self.status_combo)
        form.addRow("Notas", self.notes)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.button(QDialogButtonBox.StandardButton.Ok).setProperty("type", "primary")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        form.addRow(bb)

        outer = QVBoxLayout(self)
        outer.addWidget(make_card(form))

    def values(self):
        return {
            "id_user": self.id_user,
            "id_patient": self.patient_combo.currentData(),
            "appointment_date": self.date_edit.date().toString("yyyy-MM-dd"),
            "appointment_time": self.time_edit.time().toString("HH:mm"),
            "status": self.status_combo.currentText(),
            "notes": self.notes.toPlainText().strip() or None,
        }


# =========================================================
# LOGIN
# =========================================================

class LoginPage(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(top_accent(), 0)

        content = QHBoxLayout()
        content.setContentsMargins(28, 24, 28, 24)
        content.setSpacing(28)

        # LEFT
        left_panel = QFrame()
        left_panel.setObjectName("LeftPanel")

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setSpacing(18)

        deco_top = QHBoxLayout()
        bubble1 = QFrame()
        bubble1.setObjectName("DecorBubbleLarge")
        bubble1.setFixedSize(120, 120)
        deco_top.addWidget(bubble1, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        deco_top.addStretch()

        center_block = QVBoxLayout()
        center_block.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_block.setSpacing(14)

        brand_circle = QFrame()
        brand_circle.setObjectName("BrandCircle")
        brand_circle.setFixedSize(190, 190)

        brand_circle_layout = QVBoxLayout(brand_circle)
        brand_circle_layout.setContentsMargins(0, 0, 0, 0)
        brand_circle_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        brand_icon = QLabel("🌿")
        brand_icon.setObjectName("BrandIcon")
        brand_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_circle_layout.addWidget(brand_icon)

        left_title = QLabel("NutriLink")
        left_title.setObjectName("LeftTitle")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_sub = QLabel("Sistema de nutrición para la gestión\nde pacientes y próximas citas")
        left_sub.setObjectName("LeftSub")
        left_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_sub.setWordWrap(True)

        center_block.addWidget(brand_circle, 0, Qt.AlignmentFlag.AlignCenter)
        center_block.addWidget(left_title)
        center_block.addWidget(left_sub)

        deco_bottom = QHBoxLayout()
        bubble2 = QFrame()
        bubble2.setObjectName("DecorBubbleSmall")
        bubble2.setFixedSize(70, 70)
        bubble3 = QFrame()
        bubble3.setObjectName("DecorBubbleMedium")
        bubble3.setFixedSize(95, 95)
        deco_bottom.addWidget(bubble2, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        deco_bottom.addStretch()
        deco_bottom.addWidget(bubble3, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        left_layout.addLayout(deco_top)
        left_layout.addStretch()
        left_layout.addLayout(center_block)
        left_layout.addStretch()
        left_layout.addLayout(deco_bottom)

        # RIGHT
        right_wrap = QVBoxLayout()
        right_wrap.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(34, 34, 34, 34)
        card_layout.setSpacing(16)

        mini_logo = QLabel("NutriLink")
        mini_logo.setObjectName("MiniLogo")
        mini_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Inicio de Sesión")
        title.setObjectName("H1")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Ingresa tus credenciales para continuar")
        subtitle.setObjectName("Muted")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        email_label = QLabel("Correo electrónico")
        email_label.setObjectName("FieldLabel")
        self.email = QLineEdit()
        self.email.setPlaceholderText("correo@ejemplo.com")

        pwd_label = QLabel("Contraseña")
        pwd_label.setObjectName("FieldLabel")
        pwd_wrap, self.password = make_password_field("Contraseña")

        self.register_btn = QPushButton("¿No tienes cuenta?")
        self.register_btn.setObjectName("LinkBtn")
        self.register_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.login_btn = QPushButton("Iniciar Sesión")
        self.login_btn.setProperty("type", "primary")
        self.login_btn.setFixedHeight(48)

        card_layout.addWidget(mini_logo)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(10)
        card_layout.addWidget(email_label)
        card_layout.addWidget(self.email)
        card_layout.addWidget(pwd_label)
        card_layout.addWidget(pwd_wrap)
        card_layout.addWidget(self.register_btn, 0, Qt.AlignmentFlag.AlignRight)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.login_btn)

        self.card = make_card(card_layout, "GlassCard")
        self.card.setFixedWidth(460)

        right_wrap.addWidget(self.card, 0, Qt.AlignmentFlag.AlignCenter)

        content.addWidget(left_panel, 5)
        content.addLayout(right_wrap, 6)

        root.addLayout(content)

        self.login_btn.clicked.connect(self.do_login)
        self.register_btn.clicked.connect(self.do_register)

        self.left_panel = left_panel
        self.brand_circle = brand_circle
        self.card_widget = self.card
        self.run_animations()

    def run_animations(self):
        self.left_effect = QGraphicsOpacityEffect()
        self.left_panel.setGraphicsEffect(self.left_effect)
        self.left_effect.setOpacity(0)

        self.card_effect = QGraphicsOpacityEffect()
        self.card_widget.setGraphicsEffect(self.card_effect)
        self.card_effect.setOpacity(0)

        self.brand_effect = QGraphicsOpacityEffect()
        self.brand_circle.setGraphicsEffect(self.brand_effect)
        self.brand_effect.setOpacity(0)

        self.left_fade = QPropertyAnimation(self.left_effect, b"opacity")
        self.left_fade.setDuration(700)
        self.left_fade.setStartValue(0)
        self.left_fade.setEndValue(1)

        self.card_fade = QPropertyAnimation(self.card_effect, b"opacity")
        self.card_fade.setDuration(800)
        self.card_fade.setStartValue(0)
        self.card_fade.setEndValue(1)

        self.brand_fade = QPropertyAnimation(self.brand_effect, b"opacity")
        self.brand_fade.setDuration(950)
        self.brand_fade.setStartValue(0)
        self.brand_fade.setEndValue(1)

        card_start = self.card_widget.pos() + QPoint(40, 0)
        card_end = self.card_widget.pos()
        self.card_slide = QPropertyAnimation(self.card_widget, b"pos")
        self.card_slide.setDuration(800)
        self.card_slide.setStartValue(card_start)
        self.card_slide.setEndValue(card_end)
        self.card_slide.setEasingCurve(QEasingCurve.Type.OutCubic)

        brand_start = self.brand_circle.pos() + QPoint(-25, 0)
        brand_end = self.brand_circle.pos()
        self.brand_slide = QPropertyAnimation(self.brand_circle, b"pos")
        self.brand_slide.setDuration(900)
        self.brand_slide.setStartValue(brand_start)
        self.brand_slide.setEndValue(brand_end)
        self.brand_slide.setEasingCurve(QEasingCurve.Type.OutBack)

        self.group = QParallelAnimationGroup()
        self.group.addAnimation(self.left_fade)
        self.group.addAnimation(self.card_fade)
        self.group.addAnimation(self.brand_fade)
        self.group.addAnimation(self.card_slide)
        self.group.addAnimation(self.brand_slide)
        self.group.start()

    def do_register(self):
        dlg = RegisterDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.p1.text() != dlg.p2.text():
                QMessageBox.warning(self, "Registro", "Las contraseñas no coinciden.")
                return
            try:
                auth_register(dlg.name.text().strip(), dlg.email.text().strip(), dlg.p1.text())
                QMessageBox.information(self, "Registro", "Cuenta creada correctamente.")
            except Exception as e:
                QMessageBox.warning(self, "Registro", str(e))

    def do_login(self):
        result = auth_login(self.email.text().strip(), self.password.text())
        if not result:
            QMessageBox.warning(self, "Login", "Credenciales inválidas.")
            return
        self.on_success(*result)


# =========================================================
# MAIN MENU
# =========================================================

class MainMenu(QWidget):
    def __init__(self, user_id: int, user_name: str, go_patients, go_appointments, do_logout):
        super().__init__()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(top_accent(), 0)

        body = QVBoxLayout()
        body.setContentsMargins(28, 18, 28, 24)
        body.setSpacing(18)

        # ===== Header centrado =====
        header = QVBoxLayout()
        header.setSpacing(6)
        header.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(12)
        brand_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        brand_icon = QLabel("🌿")
        brand_icon.setObjectName("MenuLeaf")

        brand_name = QLabel("NutriLink")
        brand_name.setObjectName("RightBrandTitle")

        brand_row.addWidget(brand_icon)
        brand_row.addWidget(brand_name)

        hello = QLabel(f"¡Hola,{user_name}!")
        hello.setObjectName("PageHeroTitle")
        hello.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Menú principal")
        sub.setObjectName("PageHeroSub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header.addLayout(brand_row)
        header.addWidget(hello)
        header.addWidget(sub)

        # ===== Zona central =====
        center = QHBoxLayout()
        center.setSpacing(34)
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # -------- Panel de control (izquierda) --------
        control_layout = QVBoxLayout()
        control_layout.setContentsMargins(24, 20, 24, 20)
        control_layout.setSpacing(16)

        control_title = QLabel("NutriLink Control Panel")
        control_title.setObjectName("CardTitle")
        control_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_pat = QPushButton("🌿  Pacientes")
        btn_pat.setProperty("type", "primary")
        btn_pat.setFixedHeight(56)

        btn_app = QPushButton("🗓️  Citas")
        btn_app.setFixedHeight(54)

        btn_logout = QPushButton("🚪  Cerrar sesión")
        btn_logout.setFixedHeight(54)

        control_layout.addWidget(control_title)
        control_layout.addWidget(btn_pat)
        control_layout.addWidget(btn_app)
        control_layout.addWidget(btn_logout)

        control_card = make_card(control_layout, "GlassCard")
        control_card.setFixedWidth(780)
        control_card.setMinimumHeight(320)
        control_card.setMaximumHeight(320)

        # -------- Panel derecho con círculo/logo --------
        right_wrap = QVBoxLayout()
        right_wrap.setSpacing(18)
        right_wrap.setAlignment(Qt.AlignmentFlag.AlignCenter)

        circle = QFrame()
        circle.setObjectName("MenuCircle")
        circle.setFixedSize(255, 255)

        circle_layout = QVBoxLayout(circle)
        circle_layout.setContentsMargins(0, 0, 0, 0)
        circle_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        circle_icon = QLabel("🌿")
        circle_icon.setObjectName("MenuCircleIcon")
        circle_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        circle_layout.addWidget(circle_icon)

        msg = QLabel("Gestiona pacientes, agendamientos y\nreportes de forma simples")
        msg.setObjectName("RightBrandSub")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)

        right_wrap.addWidget(circle, 0, Qt.AlignmentFlag.AlignCenter)
        right_wrap.addWidget(msg, 0, Qt.AlignmentFlag.AlignCenter)

        center.addWidget(control_card, 0, Qt.AlignmentFlag.AlignVCenter)
        center.addLayout(right_wrap)

        # ===== Footer =====
        footer = QLabel("Explora la red NutriLink | Programa una cita | Salir de NutriLink HQ")
        footer.setObjectName("CardSub")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        body.addLayout(header)
        body.addSpacing(8)
        body.addLayout(center)
        body.addSpacing(6)
        body.addWidget(footer)

        outer.addLayout(body)

        btn_pat.clicked.connect(lambda: go_patients(user_id))
        btn_app.clicked.connect(lambda: go_appointments(user_id))
        btn_logout.clicked.connect(do_logout)
# =========================================================
# PATIENTS PAGE
# =========================================================

class PatientsPage(QWidget):
    def __init__(self, id_user: int, on_back, on_logout, go_appointments=None):
        super().__init__()
        self.id_user = id_user
        self.on_back = on_back
        self.on_logout = on_logout
        self.go_appointments = go_appointments

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        pattern_top = QFrame()
        pattern_top.setObjectName("TopPatternBar")
        lay.addWidget(pattern_top, 0)

        container = QVBoxLayout()
        container.setContentsMargins(24, 18, 24, 18)
        container.setSpacing(18)

        # Header row
        header_row = QHBoxLayout()

        title = QLabel("Gestión de pacientes")
        title.setObjectName("PatientsMainTitle")

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        total_patients = len(list_patients(self.id_user))
        citas_hoy = len([
            r for r in list_upcoming_appointments(self.id_user)
            if len(r) > 2 and str(r[2]) == QDate.currentDate().toString("yyyy-MM-dd")
        ])

        card_total = make_stat_card("Total Pacientes:", str(total_patients))
        card_today = make_stat_card("Citas hoy:", str(citas_hoy))

        stats_row.addWidget(card_total)
        stats_row.addWidget(card_today)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addLayout(stats_row)

        # Search card
        search_lay = QVBoxLayout()
        search_lay.setContentsMargins(24, 24, 24, 20)
        search_lay.setSpacing(14)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar nombre o apellidos...")
        self.search.setMinimumHeight(48)
        self.search.setObjectName("SearchInput")

        search_lay.addWidget(self.search)
        search_card = make_card(search_lay, "GlassCard")

        # Action row
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        bsearch = icon_button("🔍  Buscar", "primary")
        bclear = icon_button("🧹  Limpiar")
        badd = icon_button("➕  Agregar", "success")
        bedit = icon_button("✏️  Editar")
        bdel = icon_button("🗑️  Eliminar", "danger")
        bexport = icon_button("📄  Exportar a PDF")
        back = icon_button("↩️  Volver")
        logout = icon_button("🚪  Cerrar sesión")

        for btn in (bsearch, bclear, badd, bedit, bdel, bexport, back, logout):
            actions_row.addWidget(btn)

        actions_row.addStretch()

        # Table card
        table_lay = QVBoxLayout()
        table_lay.setContentsMargins(18, 18, 18, 18)
        table_lay.setSpacing(10)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        table_lay.addWidget(self.table)
        table_card = make_card(table_lay, "PatientsTableCard")

        container.addLayout(header_row)
        container.addWidget(search_card)
        container.addLayout(actions_row)
        container.addWidget(table_card, 1)

        lay.addLayout(container, 1)

        bsearch.clicked.connect(lambda: self.refresh(self.search.text().strip()))
        bclear.clicked.connect(self._clear_search)
        badd.clicked.connect(self._add)
        bedit.clicked.connect(self._edit)
        bdel.clicked.connect(self._delete)
        bexport.clicked.connect(self._export)
        back.clicked.connect(self.on_back)
        logout.clicked.connect(self.on_logout)

        self.refresh()

    def _clear_search(self):
        self.search.clear()
        self.refresh("")

    def refresh(self, q=""):
        rows = list_patients(self.id_user, q)
        if not hasattr(self, "model"):
            self.model = PatientsModel(rows)
            self.table.setModel(self.model)
        else:
            self.model.update(rows)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _selected_id(self):
        idx = self.table.currentIndex()
        if not idx.isValid():
            return None
        return int(self.model.get_row(idx.row())[0])

    def _add(self):
        dlg = PatientDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        first = dlg.first.text().strip()
        last = dlg.last.text().strip()
        sex = dlg.sex.currentText()
        age = int(dlg.age.value())
        weight = float(dlg.weight.value())
        height = float(dlg.height.value())
        phone = dlg.phone.text().strip() or None
        email = dlg.email.text().strip() or None

        if not first or not last:
            QMessageBox.warning(self, "Paciente", "Nombre y apellidos son obligatorios.")
            return
        if email and not valid_email(email):
            QMessageBox.warning(self, "Paciente", "Correo inválido.")
            return
        if not valid_phone(phone or ""):
            QMessageBox.warning(self, "Paciente", "Teléfono inválido. Debe tener 10 dígitos.")
            return

        try:
            create_patient(self.id_user, first, last, sex, age, weight, height, phone, email)
            self.refresh(self.search.text().strip())
        except Exception as e:
            QMessageBox.critical(self, "Paciente", f"Error al agregar paciente:\n{e}")

    def _edit(self):
        pid = self._selected_id()
        if pid is None:
            QMessageBox.information(self, "Editar", "Selecciona un paciente.")
            return

        current = next((r for r in self.model.rows if r[0] == pid), None)
        if current is None:
            QMessageBox.warning(self, "Editar", "No se encontró el paciente.")
            return

        dlg = PatientDialog(self, current)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        first = dlg.first.text().strip()
        last = dlg.last.text().strip()
        sex = dlg.sex.currentText()
        age = int(dlg.age.value())
        weight = float(dlg.weight.value())
        height = float(dlg.height.value())
        phone = dlg.phone.text().strip() or None
        email = dlg.email.text().strip() or None

        if not first or not last:
            QMessageBox.warning(self, "Paciente", "Nombre y apellidos son obligatorios.")
            return
        if email and not valid_email(email):
            QMessageBox.warning(self, "Paciente", "Correo inválido.")
            return
        if not valid_phone(phone or ""):
            QMessageBox.warning(self, "Paciente", "Teléfono inválido. Debe tener 10 dígitos.")
            return

        try:
            update_patient(pid, first, last, sex, age, weight, height, phone, email)
            self.refresh(self.search.text().strip())
        except Exception as e:
            QMessageBox.critical(self, "Paciente", f"Error al editar paciente:\n{e}")

    def _delete(self):
        pid = self._selected_id()
        if pid is None:
            QMessageBox.information(self, "Eliminar", "Selecciona un paciente.")
            return

        if QMessageBox.question(self, "Confirmar", "¿Eliminar paciente seleccionado?") == QMessageBox.StandardButton.Yes:
            try:
                delete_patient(pid)
                self.refresh(self.search.text().strip())
            except Exception as e:
                QMessageBox.critical(self, "Paciente", f"Error al eliminar paciente:\n{e}")

    def _export(self):
        default_path = str(settings.PDF_EXPORT_DIR / "pacientes.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", default_path, "PDF (*.pdf)")
        if not path:
            return

        try:
            export_patients_pdf(self.model.rows, path)
            QMessageBox.information(self, "PDF", "PDF exportado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "PDF", f"Error al exportar PDF:\n{e}")


# =========================================================
# APPOINTMENTS PAGE
# =========================================================

class AppointmentsPage(QWidget):
    def __init__(self, id_user: int, on_back, on_logout):
        super().__init__()
        self.id_user = id_user
        self.on_back = on_back
        self.on_logout = on_logout

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        pattern_top = QFrame()
        pattern_top.setObjectName("TopPatternBar")
        lay.addWidget(pattern_top, 0)

        container = QVBoxLayout()
        container.setContentsMargins(24, 18, 24, 18)
        container.setSpacing(18)

        header_row = QHBoxLayout()

        title = QLabel("Próximas citas")
        title.setObjectName("PatientsMainTitle")

        total_citas = len(list_upcoming_appointments(self.id_user))
        citas_hoy = len([
            r for r in list_upcoming_appointments(self.id_user)
            if len(r) > 2 and str(r[2]) == QDate.currentDate().toString("yyyy-MM-dd")
        ])

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        stats_row.addWidget(make_stat_card("Total Citas:", str(total_citas)))
        stats_row.addWidget(make_stat_card("Citas hoy:", str(citas_hoy)))

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addLayout(stats_row)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        badd = icon_button("➕  Nueva cita", "success")
        batt = icon_button("✅  Marcar atendida")
        bcan = icon_button("🚫  Cancelar cita")
        bdel = icon_button("🗑️  Eliminar", "danger")
        back = icon_button("↩️  Volver")
        logout = icon_button("🚪  Cerrar sesión")

        for btn in (badd, batt, bcan, bdel, back, logout):
            actions_row.addWidget(btn)

        actions_row.addStretch()

        table_lay = QVBoxLayout()
        table_lay.setContentsMargins(18, 18, 18, 18)
        table_lay.setSpacing(10)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)

        table_lay.addWidget(self.table)
        table_card = make_card(table_lay, "PatientsTableCard")

        container.addLayout(header_row)
        container.addLayout(actions_row)
        container.addWidget(table_card, 1)

        lay.addLayout(container, 1)

        badd.clicked.connect(self._add)
        batt.clicked.connect(self._attended)
        bcan.clicked.connect(self._cancel)
        bdel.clicked.connect(self._delete)
        back.clicked.connect(self.on_back)
        logout.clicked.connect(self.on_logout)

        self.refresh()

    def refresh(self):
        rows = list_upcoming_appointments(self.id_user)
        if not hasattr(self, "model"):
            self.model = AppointmentsModel(rows)
            self.table.setModel(self.model)
        else:
            self.model.update(rows)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _selected_row(self):
        idx = self.table.currentIndex()
        if not idx.isValid():
            return None
        return self.model.get_row(idx.row())

    def _selected_id(self):
        row = self._selected_row()
        return None if not row else int(row[0])

    def _add(self):
        dlg = AppointmentDialog(self.id_user, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                create_appointment(**dlg.values())
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Citas", f"Error al crear cita:\n{e}")

    def _attended(self):
        row = self._selected_row()
        if not row:
            QMessageBox.information(self, "Citas", "Selecciona una cita.")
            return
        try:
            update_appointment(row[0], row[2], row[3], "Atendida", row[5])
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Citas", f"Error al actualizar cita:\n{e}")

    def _cancel(self):
        row = self._selected_row()
        if not row:
            QMessageBox.information(self, "Citas", "Selecciona una cita.")
            return
        try:
            update_appointment(row[0], row[2], row[3], "Cancelada", row[5])
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Citas", f"Error al actualizar cita:\n{e}")

    def _delete(self):
        appointment_id = self._selected_id()
        if appointment_id is None:
            QMessageBox.information(self, "Citas", "Selecciona una cita.")
            return
        if QMessageBox.question(self, "Confirmar", "¿Eliminar cita seleccionada?") == QMessageBox.StandardButton.Yes:
            try:
                delete_appointment(appointment_id)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Citas", f"Error al eliminar cita:\n{e}")


# =========================================================
# APP
# =========================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setApplicationName(settings.APP_NAME)
    app.setApplicationVersion(settings.APP_VERSION)

    init_schema()
    load_qss(str(settings.BASE_DIR / "config" / "theme.qss"))

    stack = QStackedWidget()

    def clear_stack():
        while stack.count():
            w = stack.widget(0)
            stack.removeWidget(w)
            w.deleteLater()

    def to_login():
        clear_stack()
        page = LoginPage(on_success=on_login)
        stack.addWidget(page)
        stack.setCurrentWidget(page)

    def on_login(user_id: int, user_name: str):
        clear_stack()
        page = MainMenu(
            user_id=user_id,
            user_name=user_name,
            go_patients=lambda uid: to_patients(uid),
            go_appointments=lambda uid: to_appointments(uid),
            do_logout=to_login
        )
        stack.addWidget(page)
        stack.setCurrentWidget(page)

    def to_patients(id_user: int):
        clear_stack()
        page = PatientsPage(
            id_user=id_user,
            on_back=lambda: on_login(id_user, get_user_name(id_user)),
            on_logout=to_login
        )
        stack.addWidget(page)
        stack.setCurrentWidget(page)

    def to_appointments(id_user: int):
        clear_stack()
        page = AppointmentsPage(
            id_user=id_user,
            on_back=lambda: on_login(id_user, get_user_name(id_user)),
            on_logout=to_login
        )
        stack.addWidget(page)
        stack.setCurrentWidget(page)

    stack.setMinimumSize(settings.WINDOW_MIN_WIDTH, settings.WINDOW_MIN_HEIGHT)
    stack.resize(settings.WINDOW_DEFAULT_WIDTH, settings.WINDOW_DEFAULT_HEIGHT)

    to_login()
    stack.show()
    return app.exec()