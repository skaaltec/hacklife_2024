import sys
import asyncio
from gui import MainWindow
from qasync import QEventLoop, QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Universal")
    window = MainWindow()
    window.show()

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)
    app_close = asyncio.Event()
    app.aboutToQuit.connect(app_close.set)
    event_loop.run_until_complete(app_close.wait())
    event_loop.close()
