import sys, os, re, json, numpy as np, requests, shutil
from PyQt5.QtWidgets import (QWidget, QLabel, QGridLayout, QApplication, 
                            QComboBox, QPushButton, QListWidget)
from PyQt5.QtCore import (Qt)
from PyQt5 import (QtGui, QtCore, QtWidgets)
from PyQt5.QtGui import QPixmap, QIcon
from datetime import datetime
import matplotlib.pyplot as plt
from decimal import *
from matplotlib.ticker import MultipleLocator

class App(QWidget):
    def __init__(self):
        super().__init__()
        
        symbolList = ['AAPL', 'AMZN', 'BA', 'BABA', 'DB', 'FB', 'GOOG','GOOGL', 'MSFT', 'NFLX', 'SNAP', 'TSLA', 'TWTR']
        
        def expirationDropDownChange(itemIndex):
            if itemIndex > 0:
                plotButton.setEnabled(True)
            else:
                plotButton.setEnabled(False)
        
        def onDeleteAllDataPush():
            for x in os.listdir():
                if os.path.isdir(x) and x in symbolList:
                    shutil.rmtree(x)
            resetexpirationListDropDown()
            plotButton.setEnabled(False)
        
        def resetexpirationListDropDown():
            expirationListDropDown.clear()
            expirationListDropDown.addItem("Select an expiration date")
            expirationListDropDown.setEnabled(False)      
        
        def onPlotPush():
            symbolList = []
            allPoints = []
            for x in symbolMultiList.selectedItems():
                symbolList.append(x.text())
            for symbol in symbolList:
                symbolPointsList = symbolPoints(symbol, expirationListDropDown.currentText())
                if symbolPointsList == "APIERROR":
                    self.statusLabel.setText('API error')
                    return 'ERROR'
                if symbolPointsList == "MULTIPLESTOCKFILES":
                    self.statusLabel.setText('Multiple ' + symbol +' info files found')
                    return 'ERROR'
                if symbolPointsList == "MULTIPLECHAINFILES":
                    self.statusLabel.setText('Multiple ' + symbol +' chain sheet files found')
                    return 'ERROR'
                if symbolPointsList == "NOEXPDATE":
                    self.statusLabel.setText('No ' + symbol + ' options for ' + expirationListDropDown.currentText() + ' found')
                    return 'ERROR'
                allPoints.append(symbolPointsList)
            self.statusLabel.setText("Select one or multiple symbols to plot")
            plotPoints(allPoints, symbolList, expirationListDropDown.currentText())
            
        def onGetDatesPush():
            if len(symbolMultiList.selectedItems()) == 1:
                symbol = symbolMultiList.selectedItems()[0].text()
                createDirIfNotThere(symbol)
                datesMatch = matchesFound(symbol, 'expdates', 0)
                if len(datesMatch) == 1:
                    datesFile = datesMatch[0]
                    datesTimestamp = datesFile[len(symbol)+5:-5]
                    resetexpirationListDropDown()
                    with open(symbol + '\\' + datesFile) as json_data:
                            datesJSON = json.load(json_data)
                    for (key, value) in datesJSON.items(): # get in "expirations" key of JSON
                        for(key2, value2) in value.items(): # get in "date" key of JSON
                            datesList = value2
                    for x in range(len(datesList)):
                        expirationListDropDown.addItem(datesList[x])
                    expirationListDropDown.setEnabled(True)
                    self.statusLabel.setText("Select one or multiple symbols to plot")
                elif len(datesMatch) > 1:
                    resetexpirationListDropDown()
                    self.statusLabel.setText("Multiple expiration date files found")
                elif len(datesMatch) == 0:
                    if fetchJSON(symbol, 'expdates', 0) == 'OK':
                        onGetDatesPush()
                    else:
                        self.statusLabel.setText("API or connection error")
            elif len(symbolMultiList.selectedItems()) == 0:
                self.statusLabel.setText("Select a symbol from the list first")
            else:
                self.statusLabel.setText("Select only one symbol from the list")
                
        expirationListDropDown = QComboBox()
        expirationListDropDown.addItem("Select an expiration date")
        expirationListDropDown.setEnabled(False)
        expirationListDropDown.currentIndexChanged.connect(expirationDropDownChange)
        symbolMultiList = QListWidget()
        symbolMultiList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        for x in symbolList:
            symbolMultiList.addItem(x)
        #symbolMultiList.setMaximumWidth(100)
        #symbolMultiList.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        plotButton = QPushButton('Plot')
        plotButton.clicked.connect(onPlotPush)
        plotButton.setEnabled(False)
        getDatesButton = QPushButton('Get dates')
        getDatesButton.clicked.connect(onGetDatesPush)
        deleteAllDataButton = QPushButton('Delete all data')
        deleteAllDataButton.clicked.connect(onDeleteAllDataPush)
        self.statusLabel = QLabel('')
        self.statusLabel.setAlignment(Qt.AlignCenter)
        
        grid = QGridLayout()
        grid.setSpacing(5)
        grid.setContentsMargins(5,5,5,5)
        grid.addWidget(expirationListDropDown, 1, 0, 1, 2)
        grid.addWidget(self.statusLabel, 3, 0, 1, 3, Qt.AlignCenter)
        grid.addWidget(symbolMultiList, 0, 0, 1, 3)
        grid.addWidget(getDatesButton, 1, 2, 1, 1)
        grid.addWidget(plotButton, 2, 0, 1, 2)
        grid.addWidget(deleteAllDataButton, 2, 2, 1, 1)
        
        self.statusLabel.setText('Select a symbol and get the expiration dates')
        self.setLayout(grid)
        self.setWindowTitle('Eddie')
        pixmap = QPixmap(32,32)
        pixmap.fill(QtCore.Qt.transparent)
        #self.setWindowIcon(QtGui.QIcon('eddie.ico'))
        self.setWindowIcon(QIcon(pixmap))
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowCloseButtonHint)
        self.show()
        self.setFixedSize(self.size())

def symbolPoints(symbol, expDate):
    createDirIfNotThere(symbol)
    stockMatch = matchesFound(symbol, 'stock', 0)
    if len(stockMatch) == 0:
        if fetchJSON(symbol, 'stock', 0) == "ERROR":
            return "APIERROR"
        stockMatch = matchesFound(symbol, 'stock', 0)
    elif len(stockMatch) > 1:
        # self.statusLabel.setText("More than one " + symbol + " info files found")
        return "MULTIPLESTOCKFILES"
    if len(stockMatch) == 1:
        stockFile = stockMatch[0]
        stockTimestamp = stockFile[len(symbol)+5:-5]
        
    chainMatch = matchesFound(symbol, 'chain', expDate)
    if len(chainMatch) == 0:
        if fetchJSON(symbol, 'chain', expDate) == "ERROR":
            return "APIERROR"
        chainMatch = matchesFound(symbol, 'chain', expDate)
    elif len(chainMatch) > 1:
        # self.statusLabel.setText("More than one " + symbol + " chain sheet files found")
        return "MULTIPLECHAINFILES"
    if len(chainMatch) == 1:
        chainFile = chainMatch[0]
        chainTimestamp = chainFile[len(symbol)+15:-5]
    
    with open(symbol + '\\' + stockFile) as json_data:
        stock = json.load(json_data)
        stockPrice = stock['quotes']['quote']['bid']
        
    print(symbol + " price :" + str(stockPrice))
    count = 0
    tempType = ''
    tempAsk = 0
    tempStrike = 0
    tempDesc = ''
    points = []
    with open(symbol + '\\' + chainFile) as json_data:
        chain = json.load(json_data)
    for (key, value) in chain.items(): # get in "options" key of JSON
        if value == None:
            return "NOEXPDATE"
        for(key2, value2) in value.items(): # get in "option" key of JSON
            for x in range(len(value2)): # iterate through all options in list
                for (key3, value3) in value2[x].items(): # get in every "#" key
                    if key3 == 'option_type':
                        tempType = value3
                    if key3 == 'ask':
                        tempAsk = value3
                    if key3 == 'strike':
                        tempStrike = value3
                    if key3 == 'description':
                        tempDesc = value3
                if tempType == 'call':
                    tempPoint = (Decimal(stockPrice)/Decimal(tempStrike), Decimal(tempAsk)/Decimal(tempStrike))
                    points.append([tempPoint, tempDesc])
                    count += 1
    print(str(count) + ' call options found')
    return points

def plotPoints(allPoints, symbolList, expDate):
    
    fig, sp = plt.subplots(figsize=(12, 6))
    fig.canvas.set_window_title(expDate)
    sp.set_title(expDate, fontsize=20)
    # min max lines
    x = np.linspace(0,1,10)
    plt.plot(x, x, c='g', linewidth=0.3)
    plt.plot(x+1, x, c='c', linewidth=0.3)
    # axis x axis y
    plt.axhline(y=0, c='k', linewidth = 0.1)
    plt.axvline(x=0, c='k', linewidth = 0.1)
    sp.xaxis.set_minor_locator(MultipleLocator(0.05))
    sp.yaxis.set_minor_locator(MultipleLocator(0.05))
    plt.xlabel('Stock / Strike')
    plt.ylabel('Option / Strike')
    plt.axis([0.5, 1.5, 0, 1.5])
    plt.axis('scaled')
    plt.grid(linewidth=0.2)
    
    descriptions = []
    symbolIndex = 0
    allSE = []
    allWE = []
    allSEforPick = []
    allWEforPick = []
    
    for symbol in allPoints:
        aSymbolCoordinates = []
        aSymbolDescriptions = []
        se = []
        we = []
        for point in symbol:
            aSymbolCoordinates.append(point[0])
            aSymbolDescriptions.append(point[1])
        descriptions.insert(symbolIndex, aSymbolDescriptions)
        se = [i[0] for i in aSymbolCoordinates]
        allSEforPick.insert(symbolIndex, se)
        allSE.extend(se)
        we = [i[1] for i in aSymbolCoordinates]
        allWEforPick.insert(symbolIndex, we)
        allWE.extend(we)
        sc = plt.scatter(se, we, 4, marker='o', cmap='tab20', label=symbolList[symbolIndex], picker=2)
        sc.set_gid(symbolIndex)
        symbolIndex+=1
    info, = sp.plot([], [], ' ', label="Click on a point for details")
    plt.legend(loc=2)
    
    def onPick(event):
        symbolID = event.artist.get_gid()
        pointID = event.ind[0]
        info.set_label("Last point clicked:\nx=" + str(round(allSEforPick[symbolID][pointID],5)) + "\n" + "y=" + str(round(allWEforPick[symbolID][pointID],5)) + "\n" + descriptions[symbolID][pointID])
        plt.legend(loc=2)
        plt.draw()
        
    cid = fig.canvas.mpl_connect('pick_event', onPick)
    plt.show()
        
def fetchJSON(symbol, typ, exp):
    mainURL = 'https://sandbox.tradier.com/v1/markets/'
    apikey = 'onetwothree'
    headers = {'Accept': 'application/json', 'Authorization': 'Bearer ' + apikey}
    createDirIfNotThere(symbol)
    if typ == 'stock':
        url = mainURL + 'quotes?symbols=' + symbol
        try:
            response = requests.get(url, headers=headers)
        except requests.exceptions.RequestException as e:
            #print(e)
            return("REQUESTERROR")
        if response.status_code == 200:
            with open(os.path.join(symbol,symbol+'stock'+ str(timestampNow()) +'.json'), 'w') as outfile:  
                json.dump(response.json(), outfile)
            return 'OK'
        else:
            print(response.status_code)
    elif typ == 'chain':
        url = mainURL + 'options/chains?symbol=' + symbol + '&expiration=' + exp
        try:
            response = requests.get(url, headers=headers)
        except requests.exceptions.RequestException as e:
            #print(e)
            return("REQUESTERROR")
        if response.status_code == 200:
            with open(os.path.join(symbol,symbol + exp +'chain'+ str(timestampNow()) +'.json'), 'w') as outfile:  
                json.dump(response.json(), outfile)
            return 'OK'
        else:
            print(response.status_code)
    elif typ == 'expdates':
        url = mainURL + 'options/expirations?symbol=' + symbol
        try:
            response = requests.get(url, headers=headers)
        except requests.exceptions.RequestException as e:
            #print(e)
            return("REQUESTERROR")
        if response.status_code == 200:
            with open(os.path.join(symbol,symbol+'dates'+ str(timestampNow()) +'.json'), 'w') as outfile:  
                json.dump(response.json(), outfile)
            return 'OK'
        else:
            print(response.status_code)
    return 'APIERROR'

def matchesFound(symbol, typ, exp):
    symbolDirContents = os.listdir(symbol)
    if typ == 'stock':
        regex = re.compile(symbol + "stock\d{10}.json")
        match = list(filter(regex.search, symbolDirContents))
        return(match)
    elif typ == 'chain':
        regex = re.compile(symbol + exp + "chain" + "\d{10}.json")
        match = list(filter(regex.search, symbolDirContents))
        return(match)
    elif typ == 'expdates':
        regex = re.compile(symbol + "dates\d{10}.json")
        match = list(filter(regex.search, symbolDirContents))
        return(match)
        
def timestampNow():
    return int(datetime.utcnow().timestamp())
    
def createDirIfNotThere(name):
    if name not in os.listdir():
        os.mkdir(name)
    elif name in os.listdir() and not os.path.isdir(name):
        os.mkdir(name)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
    