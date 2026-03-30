from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple, Optional

from PyQt6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QPropertyAnimation,
    QParallelAnimationGroup,
    QEasingCurve,
    QPoint,
    QRect,
    QDate,
    QTime,
)
from PyQt6.QtGui import QColor, QTextCharFormat, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QStyleFactory,
    QWidget,
    QStackedWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QTableView,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QTextEdit,
    QDateEdit,
    QTimeEdit,
    QSizePolicy,
    QHeaderView,
    QScrollArea,
    QGridLayout,
)

from config import settings
from src.database.schema import init_schema
from src.auth import (
    login as auth_login,
    register as auth_register,
    valid_email,
    valid_phone,
)
from src.database import (
    list_patients,
    create_patient,
    update_patient,
    delete_patient,
    create_appointment,
    update_appointment,
    delete_appointment,
    list_upcoming_appointments,
    list_patients_basic,
    get_user_name,
)
from src.reports import export_patients_pdf


# =========================================================
# HELPERS
# =========================================================

def load_qss(path: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            app = QApplication.instance()
            if app is not None:
                app.setStyleSheet(f.read())
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


def status_badge_style(status: str) -> str:
    status = (status or "").strip().lower()
    if status == "atendida":
        return (
            "background:#dcfce7;color:#166534;border:2px solid #22c55e;"
            "border-radius:16px;padding:8px 14px;font-weight:800;"
        )
    if status == "cancelada":
        return (
            "background:#fee2e2;color:#991b1b;border:2px solid #ef4444;"
            "border-radius:16px;padding:8px 14px;font-weight:800;"
        )
    return (
        "background:#ecfccb;color:#365314;border:2px solid #84cc16;"
        "border-radius:16px;padding:8px 14px;font-weight:800;"
    )


def image_label(image_name: str, max_w: int = 240, max_h: int = 180) -> QLabel:
    lbl = QLabel()
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet("background: transparent;")

    possible_paths = [
        settings.BASE_DIR / image_name,
        settings.BASE_DIR / "assets" / image_name,
        settings.BASE_DIR / "data" / image_name,
    ]

    pixmap = QPixmap()
    for path in possible_paths:
        if Path(path).exists():
            pixmap = QPixmap(str(path))
            break

    if not pixmap.isNull():
        pixmap = pixmap.scaled(
            max_w,
            max_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        lbl.setPixmap(pixmap)
    else:
        lbl.setText("Imagen no encontrada")
        lbl.setStyleSheet(
            "background:#f0fdf4;color:#166534;border:1px dashed #22c55e;"
            "border-radius:16px;padding:20px;font-weight:700;"
        )
    return lbl


# =========================================================
# MODELS
# =========================================================

PATIENT_HEADERS = [
    "#",
    "Nombre",
    "Apellidos",
    "Sexo",
    "Edad",
    "Peso",
    "Altura",
    "Teléfono",
    "Correo",
    "IMC",
    "TMB",
    "% Grasa",
    "Peso Ideal",
]


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
        return None

    def data(self, idx: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not idx.isValid():
            return None

        row = self.rows[idx.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            if idx.column() == 0:
                return str(idx.row() + 1)
            value = row[idx.column()]
            return "" if value is None else str(value)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return int(Qt.AlignmentFlag.AlignCenter)

        return None

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
        self.setMinimumWidth(520)

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

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
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
        self.setMinimumWidth(560)

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

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
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
        self.setMinimumWidth(560)

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

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_btn = bb.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_btn.setProperty("type", "primary")
        self.ok_btn.clicked.connect(self.validate_and_accept)
        bb.rejected.connect(self.reject)
        form.addRow(bb)

        outer = QVBoxLayout(self)
        outer.addWidget(make_card(form))

        self.calendar = self.date_edit.calendarWidget()
        self.blocked_weekdays = {1, 6, 7}  # lunes, sábado, domingo

        self.date_edit.dateChanged.connect(self.on_date_changed)

        self.paint_calendar()
        self.on_date_changed(self.date_edit.date())

    def is_blocked_day(self, date: QDate) -> bool:
        return date.dayOfWeek() in self.blocked_weekdays

    def paint_calendar(self):
        if not self.calendar:
            return

        fmt_default = QTextCharFormat()

        fmt_blocked = QTextCharFormat()
        fmt_blocked.setBackground(QColor("#fecaca"))
        fmt_blocked.setForeground(QColor("#991b1b"))

        fmt_has_appointment = QTextCharFormat()
        fmt_has_appointment.setBackground(QColor("#bbf7d0"))
        fmt_has_appointment.setForeground(QColor("#166534"))

        current = self.date_edit.date()
        year = current.year()

        for month in range(1, 13):
            days = QDate(year, month, 1).daysInMonth()
            for day in range(1, days + 1):
                d = QDate(year, month, day)
                self.calendar.setDateTextFormat(d, fmt_default)

        for month in range(1, 13):
            days = QDate(year, month, 1).daysInMonth()
            for day in range(1, days + 1):
                d = QDate(year, month, day)
                if self.is_blocked_day(d):
                    self.calendar.setDateTextFormat(d, fmt_blocked)

        for row in list_upcoming_appointments(self.id_user):
            try:
                d = QDate.fromString(str(row[2]), "yyyy-MM-dd")
                if d.isValid() and d.year() == year and not self.is_blocked_day(d):
                    self.calendar.setDateTextFormat(d, fmt_has_appointment)
            except Exception:
                pass

    def on_date_changed(self, date: QDate):
        self.ok_btn.setEnabled(not self.is_blocked_day(date))

    def validate_and_accept(self):
        selected_date = self.date_edit.date()
        if self.is_blocked_day(selected_date):
            QMessageBox.warning(
                self,
                "Fecha no disponible",
                "No se pueden agendar citas en sábado, domingo o lunes."
            )
            return

        if self.patient_combo.currentData() is None:
            QMessageBox.warning(self, "Cita", "Debes seleccionar un paciente.")
            return

        self.accept()

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

        self.left_panel = QFrame()
        self.left_panel.setObjectName("LeftPanel")

        left_layout = QVBoxLayout(self.left_panel)
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

        self.brand_circle = QFrame()
        self.brand_circle.setObjectName("BrandCircle")
        self.brand_circle.setFixedSize(190, 190)

        brand_circle_layout = QVBoxLayout(self.brand_circle)
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

        center_block.addWidget(self.brand_circle, 0, Qt.AlignmentFlag.AlignCenter)
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

        self.card_widget = make_card(card_layout, "GlassCard")
        self.card_widget.setFixedWidth(460)

        right_wrap.addWidget(self.card_widget, 0, Qt.AlignmentFlag.AlignCenter)

        content.addWidget(self.left_panel, 5)
        content.addLayout(right_wrap, 6)
        root.addLayout(content)

        self.login_btn.clicked.connect(self.do_login)
        self.register_btn.clicked.connect(self.do_register)

    def showEvent(self, event):
        super().showEvent(event)
        self.run_animations()

    def run_animations(self):
        if getattr(self, "_anim_ran", False):
            return
        self._anim_ran = True

        self.card_effect = QGraphicsOpacityEffect()
        self.card_widget.setGraphicsEffect(self.card_effect)
        self.card_effect.setOpacity(0)

        self.brand_effect = QGraphicsOpacityEffect()
        self.brand_circle.setGraphicsEffect(self.brand_effect)
        self.brand_effect.setOpacity(0)

        final_geom = self.left_panel.geometry()
        start_geom = QRect(0, final_geom.y(), self.width() - 56, final_geom.height())

        self.expand_anim = QPropertyAnimation(self.left_panel, b"geometry")
        self.expand_anim.setDuration(850)
        self.expand_anim.setStartValue(start_geom)
        self.expand_anim.setEndValue(final_geom)
        self.expand_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        card_end = self.card_widget.pos()
        card_start = self.card_widget.pos() + QPoint(60, 0)

        self.card_slide = QPropertyAnimation(self.card_widget, b"pos")
        self.card_slide.setDuration(900)
        self.card_slide.setStartValue(card_start)
        self.card_slide.setEndValue(card_end)
        self.card_slide.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.card_fade = QPropertyAnimation(self.card_effect, b"opacity")
        self.card_fade.setDuration(850)
        self.card_fade.setStartValue(0)
        self.card_fade.setEndValue(1)

        brand_end = self.brand_circle.pos()
        brand_start = self.brand_circle.pos() + QPoint(-30, 0)

        self.brand_slide = QPropertyAnimation(self.brand_circle, b"pos")
        self.brand_slide.setDuration(950)
        self.brand_slide.setStartValue(brand_start)
        self.brand_slide.setEndValue(brand_end)
        self.brand_slide.setEasingCurve(QEasingCurve.Type.OutBack)

        self.brand_fade = QPropertyAnimation(self.brand_effect, b"opacity")
        self.brand_fade.setDuration(950)
        self.brand_fade.setStartValue(0)
        self.brand_fade.setEndValue(1)

        self.group = QParallelAnimationGroup(self)
        self.group.addAnimation(self.expand_anim)
        self.group.addAnimation(self.card_slide)
        self.group.addAnimation(self.card_fade)
        self.group.addAnimation(self.brand_slide)
        self.group.addAnimation(self.brand_fade)
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
# DASHBOARD
# =========================================================

class DashboardCard(QFrame):
    def __init__(
        self,
        title: str,
        subtitle: str,
        image_name: str,
        button_left: str,
        button_right: str,
    ):
        super().__init__()
        self.setObjectName("DashboardCard")

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(14)

        top = QVBoxLayout()
        top.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("DashboardCardTitle")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_lbl = QLabel(subtitle)
        subtitle_lbl.setObjectName("DashboardCardSubtitle")
        subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_lbl.setWordWrap(True)

        top.addWidget(title_lbl)
        top.addWidget(subtitle_lbl)

        self.image_box = image_label(image_name, 240, 180)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        self.btn_left = QPushButton(button_left)
        self.btn_right = QPushButton(button_right)

        self.btn_left.setProperty("type", "primary")
        self.btn_right.setProperty("type", "success")

        self.btn_left.setFixedHeight(46)
        self.btn_right.setFixedHeight(46)

        buttons.addWidget(self.btn_left)
        buttons.addWidget(self.btn_right)

        root.addLayout(top)
        root.addWidget(self.image_box, 1, Qt.AlignmentFlag.AlignCenter)
        root.addLayout(buttons)


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

        hello = QLabel(f"¡Hola, {user_name}!")
        hello.setObjectName("PageHeroTitle")
        hello.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Menú principal")
        sub.setObjectName("PageHeroSub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header.addLayout(brand_row)
        header.addWidget(hello)
        header.addWidget(sub)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(24)

        patients_card = DashboardCard(
            title="Gestión de Pacientes",
            subtitle="Administra la información clínica y nutricional de tus pacientes.",
            image_name="Paciente.png",
            button_left="Ver pacientes",
            button_right="Nuevo paciente",
        )

        appointments_card = DashboardCard(
            title="Calendario de Citas",
            subtitle="Consulta, agenda y controla las próximas citas nutricionales.",
            image_name="Calendario.png",
            button_left="Ver citas",
            button_right="Programar cita",
        )

        patients_card.btn_left.clicked.connect(lambda: go_patients(user_id))
        patients_card.btn_right.clicked.connect(lambda: go_patients(user_id))
        appointments_card.btn_left.clicked.connect(lambda: go_appointments(user_id))
        appointments_card.btn_right.clicked.connect(lambda: go_appointments(user_id))

        cards_row.addWidget(patients_card)
        cards_row.addWidget(appointments_card)

        logout_wrap = QHBoxLayout()
        logout_wrap.addStretch()

        logout_btn = QPushButton("🚪  Cerrar sesión")
        logout_btn.setFixedHeight(52)
        logout_btn.setMinimumWidth(260)
        logout_btn.clicked.connect(do_logout)

        logout_wrap.addWidget(logout_btn)
        logout_wrap.addStretch()

        main_card_layout = QVBoxLayout()
        main_card_layout.setContentsMargins(18, 18, 18, 18)
        main_card_layout.setSpacing(18)
        main_card_layout.addLayout(cards_row)
        main_card_layout.addLayout(logout_wrap)

        main_panel = make_card(main_card_layout, "GlassCard")

        body.addLayout(header)
        body.addWidget(main_panel, 1)

        outer.addLayout(body)


# =========================================================
# PATIENTS PAGE
# =========================================================

class PatientsPage(QWidget):
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

        title = QLabel("Gestión de pacientes")
        title.setObjectName("PatientsMainTitle")

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        total_patients = len(list_patients(self.id_user))
        citas_hoy = len(
            [
                r for r in list_upcoming_appointments(self.id_user)
                if len(r) > 2 and str(r[2]) == QDate.currentDate().toString("yyyy-MM-dd")
            ]
        )

        card_total = make_stat_card("Total Pacientes:", str(total_patients))
        card_today = make_stat_card("Citas hoy:", str(citas_hoy))

        stats_row.addWidget(card_total)
        stats_row.addWidget(card_today)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addLayout(stats_row)

        search_lay = QVBoxLayout()
        search_lay.setContentsMargins(24, 24, 24, 20)
        search_lay.setSpacing(14)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar nombre o apellidos...")
        self.search.setMinimumHeight(48)
        self.search.setObjectName("SearchInput")

        search_lay.addWidget(self.search)
        search_card = make_card(search_lay, "GlassCard")

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

        table_lay = QVBoxLayout()
        table_lay.setContentsMargins(18, 18, 18, 18)
        table_lay.setSpacing(10)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setSortingEnabled(False)

        table_lay.addWidget(self.table)
        table_card = make_card(table_lay, "PatientsTableCard")

        centered_table = QHBoxLayout()
        centered_table.addStretch()
        centered_table.addWidget(table_card, 1)
        centered_table.addStretch()

        container.addLayout(header_row)
        container.addWidget(search_card)
        container.addLayout(actions_row)
        container.addLayout(centered_table, 1)

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
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(
            self.table.model().columnCount() - 1, QHeaderView.ResizeMode.Stretch
        )

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

        if QMessageBox.question(
            self, "Confirmar", "¿Eliminar paciente seleccionado?"
        ) == QMessageBox.StandardButton.Yes:
            try:
                delete_patient(pid)
                self.refresh(self.search.text().strip())
            except Exception as e:
                QMessageBox.critical(self, "Paciente", f"Error al eliminar paciente:\n{e}")

    def _export(self):
        default_path = str(settings.PDF_EXPORT_DIR / "pacientes.pdf")
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF", default_path, "PDF (*.pdf)"
        )
        if not path:
            return

        try:
            export_patients_pdf(self.model.rows, path)
            QMessageBox.information(self, "PDF", "PDF exportado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "PDF", f"Error al exportar PDF:\n{e}")


# =========================================================
# APPOINTMENT CARD
# =========================================================

class AppointmentCard(QFrame):
    def __init__(self, row: Tuple, on_select):
        super().__init__()
        self.row_data = row
        self.on_select = on_select
        self.selected = False

        self.setObjectName("GlassCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(18)

        idx_box = QLabel(str(row[0]))
        idx_box.setFixedWidth(36)
        idx_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idx_box.setStyleSheet("font-size:24px;font-weight:900;color:#111827;background:transparent;")

        patient_box = QVBoxLayout()
        patient_box.setSpacing(4)
        patient_title = QLabel(str(row[1]))
        patient_title.setStyleSheet("font-size:22px;font-weight:800;color:#111827;background:transparent;")
        patient_sub = QLabel("Paciente registrado")
        patient_sub.setStyleSheet("font-size:13px;color:#6b7280;background:transparent;")
        patient_box.addWidget(patient_title)
        patient_box.addWidget(patient_sub)

        date_box = QVBoxLayout()
        date_box.setSpacing(4)
        date_title = QLabel("📅  Fecha")
        date_title.setStyleSheet("font-size:13px;font-weight:700;color:#374151;background:transparent;")
        date_value = QLabel(str(row[2]))
        date_value.setStyleSheet("font-size:18px;font-weight:800;color:#111827;background:transparent;")
        date_box.addWidget(date_title)
        date_box.addWidget(date_value)

        time_box = QVBoxLayout()
        time_box.setSpacing(4)
        time_title = QLabel("🕒  Hora")
        time_title.setStyleSheet("font-size:13px;font-weight:700;color:#374151;background:transparent;")
        time_value = QLabel(str(row[3]))
        time_value.setStyleSheet("font-size:18px;font-weight:800;color:#111827;background:transparent;")
        time_box.addWidget(time_title)
        time_box.addWidget(time_value)

        status_box = QVBoxLayout()
        status_box.setSpacing(4)
        status_title = QLabel("Estado")
        status_title.setStyleSheet("font-size:13px;font-weight:700;color:#374151;background:transparent;")
        self.status_value = QLabel(str(row[4]))
        self.status_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_value.setStyleSheet(status_badge_style(str(row[4])))
        status_box.addWidget(status_title)
        status_box.addWidget(self.status_value)

        notes_box = QVBoxLayout()
        notes_box.setSpacing(4)
        notes_title = QLabel("Notas")
        notes_title.setStyleSheet("font-size:13px;font-weight:700;color:#374151;background:transparent;")
        notes_text = str(row[5]) if row[5] else "Sin notas"
        if len(notes_text) > 70:
            notes_text = notes_text[:67] + "..."
        self.notes_value = QLabel(notes_text)
        self.notes_value.setWordWrap(True)
        self.notes_value.setStyleSheet("font-size:15px;color:#111827;background:transparent;")
        notes_box.addWidget(notes_title)
        notes_box.addWidget(self.notes_value)

        root.addWidget(idx_box)
        root.addLayout(patient_box, 3)
        root.addLayout(date_box, 2)
        root.addLayout(time_box, 2)
        root.addLayout(status_box, 2)
        root.addLayout(notes_box, 4)

        self.set_unselected_style()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.on_select(self)

    def set_selected(self, selected: bool):
        self.selected = selected
        if selected:
            self.setStyleSheet(
                "QFrame{background:#f0fdf4;border:2px solid #22c55e;border-radius:22px;}"
            )
        else:
            self.set_unselected_style()

    def set_unselected_style(self):
        self.setStyleSheet(
            "QFrame{background:white;border:1px solid #e5e7eb;border-radius:22px;}"
        )


# =========================================================
# APPOINTMENTS PAGE
# =========================================================

class AppointmentsPage(QWidget):
    def __init__(self, id_user: int, on_back, on_logout):
        super().__init__()
        self.id_user = id_user
        self.on_back = on_back
        self.on_logout = on_logout
        self.selected_card: Optional[AppointmentCard] = None

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

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.card_total = make_stat_card("Total Citas:", "0")
        self.card_today = make_stat_card("Citas hoy:", "0")
        stats_row.addWidget(self.card_total)
        stats_row.addWidget(self.card_today)

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

        body_lay = QVBoxLayout()
        body_lay.setContentsMargins(18, 18, 18, 18)
        body_lay.setSpacing(12)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.cards_host = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_host)
        self.cards_layout.setContentsMargins(6, 6, 6, 6)
        self.cards_layout.setSpacing(14)

        self.scroll.setWidget(self.cards_host)
        body_lay.addWidget(self.scroll)

        body_card = make_card(body_lay, "PatientsTableCard")

        container.addLayout(header_row)
        container.addLayout(actions_row)
        container.addWidget(body_card, 1)

        lay.addLayout(container, 1)

        badd.clicked.connect(self._add)
        batt.clicked.connect(self._attended)
        bcan.clicked.connect(self._cancel)
        bdel.clicked.connect(self._delete)
        back.clicked.connect(self.on_back)
        logout.clicked.connect(self.on_logout)

        self.refresh()

    def _set_selected_card(self, card: AppointmentCard):
        if self.selected_card is not None:
            self.selected_card.set_selected(False)
        self.selected_card = card
        self.selected_card.set_selected(True)

    def _selected_row(self):
        if self.selected_card is None:
            return None
        return self.selected_card.row_data

    def _selected_id(self):
        row = self._selected_row()
        return None if row is None else int(row[0])

    def refresh(self):
        rows = list_upcoming_appointments(self.id_user)

        total_citas = len(rows)
        citas_hoy = len(
            [r for r in rows if len(r) > 2 and str(r[2]) == QDate.currentDate().toString("yyyy-MM-dd")]
        )

        total_lbl = self.card_total.findChildren(QLabel)
        today_lbl = self.card_today.findChildren(QLabel)
        if len(total_lbl) >= 2:
            total_lbl[1].setText(str(total_citas))
        if len(today_lbl) >= 2:
            today_lbl[1].setText(str(citas_hoy))

        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.selected_card = None

        if not rows:
            empty = QLabel("No hay citas registradas.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                "font-size:18px;font-weight:700;color:#6b7280;background:transparent;padding:30px;"
            )
            self.cards_layout.addWidget(empty)
        else:
            for row in rows:
                card = AppointmentCard(row, self._set_selected_card)
                self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

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
        if QMessageBox.question(
            self, "Confirmar", "¿Eliminar cita seleccionada?"
        ) == QMessageBox.StandardButton.Yes:
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
            do_logout=to_login,
        )
        stack.addWidget(page)
        stack.setCurrentWidget(page)

    def to_patients(id_user: int):
        clear_stack()
        page = PatientsPage(
            id_user=id_user,
            on_back=lambda: on_login(id_user, get_user_name(id_user)),
            on_logout=to_login,
        )
        stack.addWidget(page)
        stack.setCurrentWidget(page)

    def to_appointments(id_user: int):
        clear_stack()
        page = AppointmentsPage(
            id_user=id_user,
            on_back=lambda: on_login(id_user, get_user_name(id_user)),
            on_logout=to_login,
        )
        stack.addWidget(page)
        stack.setCurrentWidget(page)

    stack.setMinimumSize(settings.WINDOW_MIN_WIDTH, settings.WINDOW_MIN_HEIGHT)
    stack.resize(settings.WINDOW_DEFAULT_WIDTH, settings.WINDOW_DEFAULT_HEIGHT)

    to_login()
    stack.show()
    return app.exec()