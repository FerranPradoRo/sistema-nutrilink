"""
NutriLink - GUI completa (PyQt6)
- Login (email/contraseña) con Ver/Ocultar
- Menú principal centrado + imagen redonda responsiva
- Pacientes: CRUD + búsqueda + exportación PDF horizontal
- Cerrar sesión
"""

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
    QGroupBox, QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
    QTextEdit, QDateEdit, QTimeEdit
)

from config import settings
from src.database.schema import init_schema
from src.auth import login as auth_login, register as auth_register, valid_email, valid_phone
from src.database import (
    list_patients, create_patient, update_patient, delete_patient,
    create_appointment, update_appointment, delete_appointment,
    list_upcoming_appointments, list_patients_basic
)
from src.reports import export_patients_pdf

# ==================== helpers ====================

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

def make_card(inner_layout) -> QFrame:
    frame = QFrame()
    frame.setObjectName("Card")
    frame.setLayout(inner_layout)
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(28)
    shadow.setOffset(0, 8)
    shadow.setColor(QColor(2, 6, 23, 40))
    frame.setGraphicsEffect(shadow)
    return frame

def make_password_field(placeholder: str = "Contraseña"):
    wrap = QWidget()
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)

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
    lay.addWidget(btn)
    return wrap, edit

# ==================== models ====================

PATIENT_HEADERS = ["#", "Nombre", "Apellidos", "Sexo", "Edad", "Peso", "Altura", "Teléfono", "Correo", "IMC", "TMB", "% Grasa", "Peso Ideal"]

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

APPOINTMENT_HEADERS = ["#", "Paciente", "Fecha", "Hora", "Estado", "Notas"]

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

# ==================== dialogs ====================

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear cuenta")

        form = QFormLayout()
        form.setContentsMargins(24, 24, 24, 24)
        form.setSpacing(12)

        title = QLabel("Crear cuenta")
        title.setObjectName("H1")
        form.addRow(title)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Nombre completo")
        self.email = QLineEdit()
        self.email.setPlaceholderText("correo@ejemplo.com")
        pwrap1, self.p1 = make_password_field("Contraseña")
        pwrap2, self.p2 = make_password_field("Confirmar contraseña")

        form.addRow("Nombre*", self.name)
        form.addRow("Correo*", self.email)
        form.addRow("Contraseña*", pwrap1)
        form.addRow("Confirmar*", pwrap2)

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
        form.setContentsMargins(24, 24, 24, 24)
        form.setSpacing(12)

        title = QLabel("Paciente")
        title.setObjectName("H1")
        form.addRow(title)

        self.first = QLineEdit()
        self.last = QLineEdit()
        self.sex = QComboBox()
        self.sex.addItems(["M", "F"])
        self.age = QSpinBox()
        self.age.setRange(0, 120)
        self.weight = QDoubleSpinBox()
        self.weight.setRange(1, 300)
        self.weight.setDecimals(2)
        self.height = QDoubleSpinBox()
        self.height.setRange(50, 250)
        self.height.setDecimals(1)
        self.phone = QLineEdit()
        self.email = QLineEdit()

        form.addRow("Nombre*", self.first)
        form.addRow("Apellidos*", self.last)
        form.addRow("Sexo*", self.sex)
        form.addRow("Edad*", self.age)
        form.addRow("Peso*", self.weight)
        form.addRow("Altura*", self.height)
        form.addRow("Teléfono", self.phone)
        form.addRow("Correo", self.email)

        if data:
            self.first.setText(data[1])
            self.last.setText(data[2])
            self.sex.setCurrentText(data[3])
            self.age.setValue(int(data[4]))
            self.weight.setValue(float(data[5]))
            self.height.setValue(float(data[6]))
            self.phone.setText(data[7] or "")
            self.email.setText(data[8] or "")

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
        form.setContentsMargins(24, 24, 24, 24)
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
        self.notes.setFixedHeight(90)

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
            "notes": self.notes.toPlainText().strip() or None
        }

# ==================== pages ====================

class LoginPage(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(top_accent())

        center = QVBoxLayout()
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.logo = QLabel("🌿")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo.setStyleSheet("font-size: 92px;")

        self.title = QLabel("NutriLink")
        self.title.setObjectName("AppTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout = QFormLayout()
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(14)

        h1 = QLabel("Iniciar sesión")
        h1.setObjectName("H1")
        card_layout.addRow(h1)

        self.email = QLineEdit()
        self.email.setPlaceholderText("Correo electrónico")
        pwd_wrap, self.password = make_password_field("Contraseña")

        card_layout.addRow(" ", self.email)
        card_layout.addRow(" ", pwd_wrap)

        btns = QHBoxLayout()
        self.login_btn = QPushButton("Entrar")
        self.login_btn.setProperty("type", "primary")
        self.register_btn = QPushButton("Crear cuenta")
        btns.addWidget(self.login_btn)
        btns.addWidget(self.register_btn)
        card_layout.addRow(btns)

        self.card = make_card(card_layout)
        self.card.setFixedWidth(470)

        center.addWidget(self.logo)
        center.addWidget(self.title)
        center.addSpacing(6)
        center.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignHCenter)

        root.addLayout(center)

        self.login_btn.clicked.connect(self.do_login)
        self.register_btn.clicked.connect(self.do_register)

        self.run_animations()

    def run_animations(self):
        self.logo_effect = QGraphicsOpacityEffect()
        self.logo.setGraphicsEffect(self.logo_effect)
        self.logo_effect.setOpacity(0)

        self.card_effect = QGraphicsOpacityEffect()
        self.card.setGraphicsEffect(self.card_effect)
        self.card_effect.setOpacity(0)

        self.logo_anim = QPropertyAnimation(self.logo_effect, b"opacity")
        self.logo_anim.setDuration(700)
        self.logo_anim.setStartValue(0)
        self.logo_anim.setEndValue(1)

        start_pos = self.card.pos() + QPoint(0, 35)
        end_pos = self.card.pos()

        self.card_move = QPropertyAnimation(self.card, b"pos")
        self.card_move.setDuration(800)
        self.card_move.setStartValue(start_pos)
        self.card_move.setEndValue(end_pos)
        self.card_move.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.card_fade = QPropertyAnimation(self.card_effect, b"opacity")
        self.card_fade.setDuration(800)
        self.card_fade.setStartValue(0)
        self.card_fade.setEndValue(1)

        self.group = QParallelAnimationGroup()
        self.group.addAnimation(self.logo_anim)
        self.group.addAnimation(self.card_move)
        self.group.addAnimation(self.card_fade)
        self.group.start()

    def do_register(self):
        dlg = RegisterDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                auth_register(
                    dlg.name.text().strip(),
                    dlg.email.text().strip(),
                    dlg.p1.text()
                )
                QMessageBox.information(self, "Registro", "Cuenta creada correctamente.")
            except Exception as e:
                QMessageBox.warning(self, "Registro", str(e))

    def do_login(self):
        result = auth_login(self.email.text().strip(), self.password.text())
        if not result:
            QMessageBox.warning(self, "Login", "Credenciales inválidas.")
            return
        self.on_success(*result)

class MainMenu(QWidget):
    def __init__(self, user_id: int, user_name: str, go_patients, go_appointments, do_logout):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(top_accent())

        body = QVBoxLayout()
        body.setContentsMargins(40, 40, 40, 40)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)

        leaf = QLabel("🌿")
        leaf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        leaf.setStyleSheet("font-size: 88px;")

        hello = QLabel(f"¡Hola, {user_name}!")
        hello.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hello.setObjectName("AppTitle")

        sub = QLabel("Menú Principal")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setObjectName("AppSubtitle")

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(14)

        btn_pat = QPushButton("Pacientes")
        btn_pat.setProperty("type", "primary")
        btn_pat.setFixedHeight(54)

        btn_app = QPushButton("Citas")
        btn_app.setProperty("type", "success")
        btn_app.setFixedHeight(54)

        btn_logout = QPushButton("Cerrar sesión")
        btn_logout.setFixedHeight(54)

        card_layout.addWidget(btn_pat)
        card_layout.addWidget(btn_app)
        card_layout.addWidget(btn_logout)

        card = make_card(card_layout)
        card.setFixedWidth(460)

        body.addWidget(leaf)
        body.addWidget(hello)
        body.addWidget(sub)
        body.addSpacing(6)
        body.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)

        outer.addLayout(body)

        btn_pat.clicked.connect(lambda: go_patients(user_id))
        btn_app.clicked.connect(lambda: go_appointments(user_id))
        btn_logout.clicked.connect(do_logout)

class PatientsPage(QWidget):
    def __init__(self, id_user: int, on_back, on_logout):
        super().__init__()
        self.id_user = id_user
        self.on_back = on_back
        self.on_logout = on_logout

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(top_accent())

        inner = QVBoxLayout()
        inner.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Gestión de pacientes")
        title.setObjectName("H1")
        inner.addWidget(title)

        tb = QToolBar()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar nombre/apellidos...")
        bsearch = QPushButton("Buscar")
        bsearch.setProperty("type", "primary")
        bclear = QPushButton("Limpiar")
        badd = QPushButton("Agregar")
        badd.setProperty("type", "success")
        bedit = QPushButton("Editar")
        bdel = QPushButton("Eliminar")
        bdel.setProperty("type", "danger")
        bexport = QPushButton("Exportar a PDF")
        back = QPushButton("Volver")
        logout = QPushButton("Cerrar sesión")

        for w in (self.search, bsearch, bclear, badd, bedit, bdel, bexport, back, logout):
            tb.addWidget(w)

        inner.addWidget(tb)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)

        box = QVBoxLayout()
        box.setContentsMargins(12, 12, 12, 12)
        box.addWidget(self.table)

        inner.addWidget(make_card(box))
        lay.addLayout(inner)

        bsearch.clicked.connect(lambda: self.refresh(self.search.text().strip()))
        bclear.clicked.connect(lambda: (self.search.clear(), self.refresh("")))
        badd.clicked.connect(self._add)
        bedit.clicked.connect(self._edit)
        bdel.clicked.connect(self._delete)
        bexport.clicked.connect(self._export)
        back.clicked.connect(self.on_back)
        logout.clicked.connect(self.on_logout)

        self.refresh()

    def refresh(self, q=""):
        rows = list_patients(self.id_user, q)
        if not hasattr(self, "model"):
            self.model = PatientsModel(rows)
            self.table.setModel(self.model)
        else:
            self.model.update(rows)
        self.table.resizeColumnsToContents()

    def _selected_id(self):
        idx = self.table.currentIndex()
        if not idx.isValid():
            return None
        return int(self.model.get_row(idx.row())[0])

    def _add(self):
        dlg = PatientDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.email.text().strip() and not valid_email(dlg.email.text().strip()):
                QMessageBox.warning(self, "Paciente", "Correo inválido.")
                return
            if not valid_phone(dlg.phone.text().strip()):
                QMessageBox.warning(self, "Paciente", "Teléfono inválido. Debe tener 10 dígitos.")
                return

            create_patient(
                self.id_user,
                dlg.first.text().strip(),
                dlg.last.text().strip(),
                dlg.sex.currentText(),
                int(dlg.age.value()),
                float(dlg.weight.value()),
                float(dlg.height.value()),
                dlg.phone.text().strip() or None,
                dlg.email.text().strip() or None,
            )
            self.refresh(self.search.text().strip())

    def _edit(self):
        pid = self._selected_id()
        if pid is None:
            QMessageBox.information(self, "Editar", "Selecciona un paciente.")
            return

        current = next((r for r in self.model.rows if r[0] == pid), None)
        dlg = PatientDialog(self, current)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.email.text().strip() and not valid_email(dlg.email.text().strip()):
                QMessageBox.warning(self, "Paciente", "Correo inválido.")
                return
            if not valid_phone(dlg.phone.text().strip()):
                QMessageBox.warning(self, "Paciente", "Teléfono inválido. Debe tener 10 dígitos.")
                return

            update_patient(
                pid,
                dlg.first.text().strip(),
                dlg.last.text().strip(),
                dlg.sex.currentText(),
                int(dlg.age.value()),
                float(dlg.weight.value()),
                float(dlg.height.value()),
                dlg.phone.text().strip() or None,
                dlg.email.text().strip() or None,
            )
            self.refresh(self.search.text().strip())

    def _delete(self):
        pid = self._selected_id()
        if pid is None:
            QMessageBox.information(self, "Eliminar", "Selecciona un paciente.")
            return
        if QMessageBox.question(self, "Confirmar", "¿Eliminar paciente seleccionado?") == QMessageBox.StandardButton.Yes:
            delete_patient(pid)
            self.refresh(self.search.text().strip())

    def _export(self):
        default_path = str(settings.PDF_EXPORT_DIR / "pacientes.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", default_path, "PDF (*.pdf)")
        if not path:
            return
        export_patients_pdf(self.model.rows, path)
        QMessageBox.information(self, "PDF", "PDF exportado correctamente.")

class AppointmentsPage(QWidget):
    def __init__(self, id_user: int, on_back, on_logout):
        super().__init__()
        self.id_user = id_user
        self.on_back = on_back
        self.on_logout = on_logout

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(top_accent())

        inner = QVBoxLayout()
        inner.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Próximas citas")
        title.setObjectName("H1")
        inner.addWidget(title)

        tb = QToolBar()
        badd = QPushButton("Nueva cita")
        badd.setProperty("type", "success")
        bmark = QPushButton("Marcar atendida")
        bcancel = QPushButton("Cancelar cita")
        bdel = QPushButton("Eliminar")
        bdel.setProperty("type", "danger")
        back = QPushButton("Volver")
        logout = QPushButton("Cerrar sesión")

        for w in (badd, bmark, bcancel, bdel, back, logout):
            tb.addWidget(w)

        inner.addWidget(tb)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)

        box = QVBoxLayout()
        box.setContentsMargins(12, 12, 12, 12)
        box.addWidget(self.table)

        inner.addWidget(make_card(box))
        lay.addLayout(inner)

        badd.clicked.connect(self._add)
        bmark.clicked.connect(self._mark_attended)
        bcancel.clicked.connect(self._cancel)
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

    def _selected_id(self):
        idx = self.table.currentIndex()
        if not idx.isValid():
            return None
        return int(self.model.get_row(idx.row())[0])

    def _selected_row(self):
        idx = self.table.currentIndex()
        if not idx.isValid():
            return None
        return self.model.get_row(idx.row())

    def _add(self):
        dlg = AppointmentDialog(self.id_user, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            create_appointment(**dlg.values())
            self.refresh()

    def _mark_attended(self):
        row = self._selected_row()
        if not row:
            QMessageBox.information(self, "Citas", "Selecciona una cita.")
            return
        update_appointment(row[0], row[2], row[3], "Atendida", row[5])
        self.refresh()

    def _cancel(self):
        row = self._selected_row()
        if not row:
            QMessageBox.information(self, "Citas", "Selecciona una cita.")
            return
        update_appointment(row[0], row[2], row[3], "Cancelada", row[5])
        self.refresh()

    def _delete(self):
        appointment_id = self._selected_id()
        if appointment_id is None:
            QMessageBox.information(self, "Citas", "Selecciona una cita.")
            return
        if QMessageBox.question(self, "Confirmar", "¿Eliminar cita seleccionada?") == QMessageBox.StandardButton.Yes:
            delete_appointment(appointment_id)
            self.refresh()

# ==================== app ====================

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
            user_id,
            user_name,
            go_patients=lambda uid: to_patients(uid),
            go_appointments=lambda uid: to_appointments(uid),
            do_logout=to_login
        )
        stack.addWidget(page)
        stack.setCurrentWidget(page)

    def to_patients(id_user: int):
        clear_stack()
        page = PatientsPage(id_user=id_user, on_back=lambda: on_login(id_user, _get_name(id_user)), on_logout=to_login)
        stack.addWidget(page)
        stack.setCurrentWidget(page)

    def to_appointments(id_user: int):
        clear_stack()
        page = AppointmentsPage(id_user=id_user, on_back=lambda: on_login(id_user, _get_name(id_user)), on_logout=to_login)
        stack.addWidget(page)
        stack.setCurrentWidget(page)

    def _get_name(id_user: int):
        # lookup rápido desde email no es ideal, pero suficiente para este flujo
        from src.database.connection import get_conn
        conn = get_conn()
        cur = conn.execute("SELECT name FROM users WHERE id_user = ?", (id_user,))
        row = cur.fetchone()
        conn.close()
        return row["name"] if row else "Usuario"

    stack.setMinimumSize(settings.WINDOW_MIN_WIDTH, settings.WINDOW_MIN_HEIGHT)
    stack.resize(settings.WINDOW_DEFAULT_WIDTH, settings.WINDOW_DEFAULT_HEIGHT)

    to_login()
    stack.show()
    return app.exec()