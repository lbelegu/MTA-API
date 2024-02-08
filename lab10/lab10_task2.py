import sys
from PyQt6.QtCore import Qt, QPoint, QRect, QSize
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import \
    (QApplication, QHBoxLayout, QLabel, QLayout, QMainWindow,
     QVBoxLayout, QSizePolicy, QWidget, QPushButton, QStyle)

from lab10_task1 import MTAFeed

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('MTA Subway Status')
        self.resize(600, 430)

        ## Setup the central widget
        widget = QWidget()
        central = QVBoxLayout()
        central.setSpacing(1)
        central.setContentsMargins(0,0,0,0)
        widget.setLayout(central)
        self.setCentralWidget(widget)

        self.feed = MTAFeed()

        ## Need to have a Service Status label
        title = QLabel('Service Status')
        title.setContentsMargins(10,10,10,10)
        title.setStyleSheet('color: #002d7c;background:white;'
                            'font-family: Arial; font-size: 24px; font-weight: bold;')
        self.lastRefresh = QLabel(self.feed.getRefreshTime().isoformat(' ')[:19])
        self.lastRefresh.setStyleSheet('color: #002d7c;background:white;'
                            'font-family: Arial; font-size: 16px; font-weight: bold;')

        refresh = QPushButton()
        refresh.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        refresh.setStyleSheet('color: #002d7c;background:white;'
                            'font-family: Arial; font-size: 24px; font-weight: bold;')
        refresh.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        refresh.clicked.connect(self.reload)

        header = QHBoxLayout()
        header.setSpacing(10)
        header.addWidget(title, 1)
        header.addWidget(self.lastRefresh)
        header.addWidget(refresh)
        central.addLayout(header)

        ## A horizontal layout to hold left (active) and right (non-active) alerts
        self.layoutAlerts = QHBoxLayout()
        self.layoutAlerts.setSpacing(0)
        central.addLayout(self.layoutAlerts)
        central.addStretch()

        self.layoutActive = QVBoxLayout()
        self.layoutAlerts.addLayout(self.layoutActive)


        self.layoutActive.setSpacing(1)        
        #self.feed = MTAFeed()
        for stat, lines in self.feed.items():
            self.layoutActive.addWidget(AlertBoard(stat, sorted(lines)))

        self.layoutAlerts.addWidget(AlertBoard('Non Active Alerts', sorted(self.feed['Non Active Alerts']), False))
        self.adjustSize()

        self.resize(600, self.height())

    # BUTTON FUNCTION
    def reload(self):

        self.feed.refresh()
        self.lastRefresh.setText(self.feed.getRefreshTime().isoformat(' ')[:19])

        # clear the baord
        for i in range(self.layoutActive.count()):
            self.layoutActive.takeAt(0).widget().deleteLater()
        self.layoutAlerts.takeAt(1).widget().deleteLater()
        
        # update the timestamp
        self.feed.refresh()
        self.lastRefresh.setText(self.feed.getRefreshTime().isoformat(' ')[:19])
        
        # add in the most current alerts/lines
        for stat,lines in self.feed.items():
            self.layoutActive.addWidget(AlertBoard(stat, sorted(lines)))

        self.layoutAlerts.addWidget(AlertBoard('Non Active Alerts', sorted(self.feed['Non Active Alerts']), False))
        self.adjustSize()

        self.resize(600, self.height())
        

class AlertBoard(QWidget):

    def __init__(self, title, lines, active=True):
        super().__init__()
        if active:
            palette = self.palette()
            palette.setColor(QPalette.ColorRole.Window, QColor('white'))
            self.setPalette(palette)
            self.setAutoFillBackground(True)

        label = QLabel(title)
        label.setStyleSheet('color: #002d7c; font-family: Arial; font-size: 16px; font-weight: bold;')

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        
        layoutLines = FlowLayout()
        layout.addLayout(layoutLines)
        for line in lines:
            layoutLines.addWidget(QSvgWidget(f'subway_signs/{line}.svg'))
        layout.addStretch()

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)

        self.setSpacing(spacing)

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        return Qt.Orientation(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margin, _, _, _ = self.getContentsMargins()

        size += QSize(2 * margin, 2 * margin)
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton, Qt.Orientation.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton, Qt.Orientation.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()        

if __name__=='__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()