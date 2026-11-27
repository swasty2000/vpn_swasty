from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QMessageBox,
)
from PySide6.QtCore import Qt, QThread, Signal

from app.ui.styles import APP_STYLE
from app.core.vpn_client import VPNManager


class VPNWorker(QThread):
    """Фоновый поток для подключения, чтобы интерфейс не зависал."""
    connected_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, manager: VPNManager):
        super().__init__()
        self.manager = manager

    def run(self):
        try:
            new_ip = self.manager.connect()
            self.connected_signal.emit(new_ip)
        except Exception as e:
            self.error_signal.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Swasty VPN")
        self.setMinimumSize(950, 620)
        self.resize(1100, 720)

        self.connected = False

        # Настройки подключения (позже замените IP на адрес вашего VPS)
        self.server_ip = "127.0.0.1"
        self.vpn_manager = VPNManager(
            server_url=f"http://{self.server_ip}:8000",
            api_token="swasty_secret_key_998877",  # Должен совпадать с API_SECRET_TOKEN в server/.env
            client_name="swasty_pc",
        )

        self.setStyleSheet(APP_STYLE)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(25, 30, 25, 25)

        logo = QLabel("◈  SWASTY")
        logo.setObjectName("logo")

        subtitle = QLabel("VPN CLIENT")
        subtitle.setObjectName("subtitle")

        sidebar_layout.addWidget(logo)
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(45)

        for name in ["Dashboard", "Servers", "Statistics", "Settings"]:
            item = QPushButton(name)
            item.setObjectName("navButton")
            sidebar_layout.addWidget(item)

        sidebar_layout.addStretch()

        version = QLabel("SWASTY VPN  •  v0.1.0")
        version.setObjectName("version")
        sidebar_layout.addWidget(version)

        # Main content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(45, 40, 45, 35)
        content_layout.setSpacing(20)

        header = QLabel("Dashboard")
        header.setObjectName("heading")

        description = QLabel("Manage your secure connection")
        description.setObjectName("description")

        content_layout.addWidget(header)
        content_layout.addWidget(description)

        content_layout.addSpacing(30)

        status_card = QFrame()
        status_card.setObjectName("card")

        card_layout = QVBoxLayout(status_card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(15)

        status_label = QLabel("CONNECTION STATUS")
        status_label.setObjectName("muted")

        self.status = QLabel("Disconnected")
        self.status.setObjectName("status")

        self.status_description = QLabel(
            "Your VPN tunnel is currently inactive"
        )
        self.status_description.setObjectName("description")

        self.connect_button = QPushButton("Connect")
        self.connect_button.setObjectName("connectButton")
        self.connect_button.setFixedHeight(52)
        self.connect_button.clicked.connect(self.toggle_connection)

        card_layout.addWidget(status_label)
        card_layout.addWidget(self.status)
        card_layout.addWidget(self.status_description)
        card_layout.addSpacing(15)
        card_layout.addWidget(self.connect_button)

        content_layout.addWidget(status_card)

        info_card = QFrame()
        info_card.setObjectName("card")

        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(25, 25, 25, 25)

        info_title = QLabel("Connection information")
        info_title.setObjectName("sectionTitle")

        self.server_label = QLabel(f"Server: {self.server_ip}")
        self.ip_label = QLabel("IP address: Not checked")
        self.protocol_label = QLabel("Protocol: AmneziaWG")

        for label in [
            info_title,
            self.server_label,
            self.ip_label,
            self.protocol_label,
        ]:
            info_layout.addWidget(label)

        content_layout.addWidget(info_card)
        content_layout.addStretch()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

    def toggle_connection(self):
        if not self.connected:
            # Блокируем кнопку на время подключения
            self.connect_button.setEnabled(False)
            self.connect_button.setText("Connecting...")
            self.status.setText("Connecting...")
            self.status_description.setText("Fetching config and starting tunnel...")

            self.worker = VPNWorker(self.vpn_manager)
            self.worker.connected_signal.connect(self.on_connected)
            self.worker.error_signal.connect(self.on_connection_error)
            self.worker.start()
        else:
            self.vpn_manager.disconnect()
            self.connected = False
            self.status.setText("Disconnected")
            self.status_description.setText("Your VPN tunnel is currently inactive")
            self.ip_label.setText("IP address: Not checked")
            self.connect_button.setText("Connect")

    def on_connected(self, new_ip: str):
        self.connected = True
        self.connect_button.setEnabled(True)
        self.status.setText("Connected")
        self.status_description.setText("Your traffic is encrypted via AmneziaWG")
        self.ip_label.setText(f"IP address: {new_ip}")
        self.connect_button.setText("Disconnect")

    def on_connection_error(self, error_message: str):
        self.connected = False
        self.connect_button.setEnabled(True)
        self.status.setText("Disconnected")
        self.status_description.setText("Connection failed")
        self.connect_button.setText("Connect")
        QMessageBox.warning(self, "Connection Error", f"Не удалось подключиться:\n{error_message}")