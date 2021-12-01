import os
import os.path
import discord
import datetime
from datetime import date, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
SHEETSCOPES = ['https://www.googleapis.com/auth/spreadsheets']

DRIVESCOPES = ['https://www.googleapis.com/auth/drive']
CALENDARSCOPES = ['https://www.googleapis.com/auth/calendar']
OAUTHSCOPES = DRIVESCOPES+CALENDARSCOPES

KEY = 'DeeriocaPuff.json'       #Credentials
OKEY = 'NewKey.json'          #OUATH ACC
DRIVETOKEN = 'DRIVETOKEN.json'
CALENDARTOKEN = 'CALENDARTOKEN.json'

class MyClient (discord.Client):
    SampleSheetID = '1stNO-oaMm6ytYjnAv3Do4hyZsd04wxAHnTwTppdX_sk'
    SampleSheetRange = 'Employee Schedule'

    OutputSheetID = '1uVDrDtwwO8vjqdqNrBzLsJZbznSmm-Vp-8wH0iA9cKA'
    OutputSheetRange = 'Sheet1'
    WorkerList = [[],[]]

    fileID = '18Rb-Tm6eQUoEDwIvzw_2pg8ImWPorSoD'

    TIMEZONE = 'Canada/Eastern' #FOR CANADA HAMILTON

    ListofYes = ['x','x0.5','OC','T']
    pos = [0,0]

#SHEETS ############################################################################################
    #The sheets apis are accessed through credentials account, unlike the drive and calendar apis, which are through OAuth clients
    def loadSheetsAPI(self):    #DONE               
        creds1 = service_account.Credentials.from_service_account_file(KEY, scopes = SHEETSCOPES)
        sheetsAPI = build('sheets', 'v4', credentials=creds1)
        return sheetsAPI
    #updated
    def sheetCopyPaste(self, InputSheet = str): #NEED LOAD CALENDAR   
        
        sheet = self.loadSheetsAPI().spreadsheets()
        result = sheet.values().get(spreadsheetId= InputSheet, range= self.SampleSheetRange).execute()
        values = result.get('values', [])                          

        body = {'values': values}

        result = self.loadSheetsAPI().spreadsheets().values().update(
            spreadsheetId=self.OutputSheetID, range=self.OutputSheetRange,
            valueInputOption="USER_ENTERED", body=body).execute()
        self.updateWorkerList()
        print('execute sheetCopyPaste')       
    #updated
    def sheetGetDate(self, sheetID):    #DONE
        sheet = self.loadSheetsAPI().spreadsheets()
        result = sheet.values().get(spreadsheetId= sheetID, range= 'O4').execute()
        values = result.get('values', []) 
        Date = values
        return Date[0][0]
    #updated
    def getPersonalSchedule (self, Worker = str, t = int):     #updateWorkerList First      
        sheet = self.loadSheetsAPI().spreadsheets() 
        
        pos = self.pos[t] + self.WorkerList[t].index(Worker)

        range = str(pos)+':'+str(pos)
        result = sheet.values().get(spreadsheetId= self.OutputSheetID, range= range).execute()
        data = result.get('values', [])
        while(len(data[0])<119):
            data[0].append('')
        return data[0]   
    #updated
    def updateWorkerList(self):
        self.WorkerList[0].clear()
        self.WorkerList[1].clear()
        sheet = self.loadSheetsAPI().spreadsheets()
        result = sheet.values().get(spreadsheetId= self.OutputSheetID, range= 'C:C').execute()
        values = result.get('values', [])
        roll1 = 0
        roll2 = False
        counter = 0
        for y in values:
            counter +=1
            if y == ['Target Coverage'] and roll2 == True:
                roll2 = False
                break
            if roll2 == True:
                x = y[0].split(' ')
                if x[0] == 'Vicky':
                    self.pos[1] = counter
                self.WorkerList[1].append(x[0])
            if y == ['Employee Name'] and roll1 == 2:
                roll2 = True

            if y == ['Target Coverage']:
                roll1 = 2

            if roll1 == 1:
                x = y[0].split(' ')
                if x[0] == 'Vicky':
                    self.pos[0] = counter
                self.WorkerList[0].append(x[0])
            if y == ['Employee Name'] and roll1 == 0:
                roll1 = 1
    #updated

#CALENDAR#############################################################################
    def loadCalendarAPI(self):
        creds = None
        if os.path.exists(CALENDARTOKEN):
            creds = Credentials.from_authorized_user_file(CALENDARTOKEN, CALENDARSCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    OKEY, CALENDARSCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(CALENDARTOKEN, 'w') as token:
                token.write(creds.to_json())
        #creds = service_account.Credentials.from_service_account_file(KEY, scopes = CALENDARSCOPES)
        calendarAPI = build('calendar', 'v3', credentials=creds)
        return calendarAPI
   
    def workerCalendarTitle(self, worker = str):
        CalendarTitle = 'Alley Schedule -'+ worker
        return CalendarTitle    
    
    def updateCalendarList(self):
        self.deleteCalendars()
        self.createCalendar()

        
    def createCalendar(self):
        for z in range(2):
            calendar_list = self.loadCalendarAPI().calendarList().list().execute()
            calendarsList = calendar_list['items']
            for worker in self.WorkerList[z]:                   #add calendars for workers
                calendarExist = False                             #does his calendar exist?
                for calendar in calendarsList:
                    if calendar['summary'] == self.workerCalendarTitle(worker):
                        calendarExist = True                      #yes!
                        break
                if calendarExist == False:     
                                        #No :(
                    created_calendar_data = {
                        'summary': self.workerCalendarTitle(worker),
                        'timeZone': self.TIMEZONE
                    }
                    created_calendar = self.loadCalendarAPI().calendars().insert(body=created_calendar_data).execute()
                    rule = {
                    "role": "reader",
                    "scope": {
                        "type": "default"
                    }
                    }
                    created_rule = self.loadCalendarAPI().acl().insert(calendarId=created_calendar['id'], body=rule).execute()
                    print('Created: '+created_calendar['summary'])
        print('createCalendars executed')

    def deleteCalendars(self):

        calendar_list = self.loadCalendarAPI().calendarList().list().execute()
        calendarsList = calendar_list['items']
        
        for calendar in calendarsList:                   #Delete calendars with no workers
            workerExist = False                           #does worker exist?
            for worker in self.WorkerList[1]:
                    
                if calendar['summary'] == self.workerCalendarTitle(worker) :
                    workerExist = True                      #yes!
                    break
                
            
            if workerExist == False:                          #No :(
                if calendar['summary'] != 'puffsuperiority@gmail.com':
                        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
                        print('Getting the upcoming 10 events')
                        events_result = self.loadCalendarAPI().events().list(calendarId=calendar['id'], timeMin=now,
                                                            maxResults=10, singleEvents=True,
                                                            orderBy='startTime').execute()
                        events = events_result.get('items', [])

                        if not events:
                            print('Delete: '+calendar['summary'])
                            self.loadCalendarAPI().calendars().delete(calendarId = calendar['id']).execute()

        print('deleteCalendars executed')
    
    def updateEvents(self,worker = str, calendarID = str, t = int):

        startDate = self.sheetGetDate(self.OutputSheetID)               #convert date
        y = startDate.split('-')
        datetime_object = datetime.datetime.strptime(y[1], "%b")
        startDateData = date(year = 2000+ int(y[2]), month = int(datetime_object.month), day = int(y[0]))
        data = self.getPersonalSchedule(worker, t) 
        
        print(len(data))
        print (data)
        description = ''
        for x in data:
            if x.startswith(worker):
                pos = data.index(x)   
            
                                            #might error idk 
        for weekday in range(7):
            Date = startDateData + timedelta(days = (1*weekday)+(t*7))
            workStart = 0
            workEnd = 0
            isWorking = False

            for hours in range(14):
                pos+=1
                if data[pos] in self.ListofYes and isWorking ==False :                    #startworking
                    isWorking = True
                    if  data[pos].startswith('OC'):
                        description = 'On Call!'
                    if data[pos].startswith('T'):
                        description = 'Training!'

                    if hours == 0:
                        workStartTime = datetime.datetime(year=Date.year, month=Date.month, day=Date.day, hour=10, minute=30, second=0)
                    else:
                        if data[pos] == 'x0.5':
                            workStartTime = datetime.datetime(year=Date.year, month=Date.month, day=Date.day, hour=(10+hours), minute=30, second=0)
                        else:
                            workStartTime = datetime.datetime(year=Date.year, month=Date.month, day=Date.day, hour=(10+hours), minute=0, second=0)
                    workStart = workStartTime.isoformat()
                
                if data[pos] in self.ListofYes and isWorking ==True :
                        if not (data[pos+1] in self.ListofYes):
                            workEnd = datetime.datetime(year=Date.year, month=Date.month, day=Date.day,hour=(10+hours), minute=59, second=59).isoformat()
            if isWorking == True:
                event = {
                'summary': 'Alley '+worker+' '+description+str(weekday),
                'location': 'Alley hamilton',
                'start': {
                    'dateTime': workStart,
                    'timeZone': self.TIMEZONE,
                },
                'end': {
                    'dateTime': workEnd,
                    'timeZone': self.TIMEZONE,
                },
                "anyoneCanAddSelf": 'True',

                'visibility' : 'public'
                }
                self.loadCalendarAPI().events().insert(calendarId = calendarID, body = event).execute()
            pos+=2
    #updated, need test
    def updateAllEvents(self):      #updateCalendarList first
            calendar_list = self.loadCalendarAPI().calendarList().list().execute()
            calendarsList = calendar_list['items']
            for z in range(2):
                for worker in self.WorkerList[z]:
                    print(worker + ' at week ' + str(z))
                    for calendar in calendarsList:
                        if calendar['summary'] == self.workerCalendarTitle(worker):
                            self.updateEvents(worker, calendar['id'], z)
                            break
                    print("updated calendar at week "+ str(z))
                print("head to next week")
            print('eventUpdates executed')

#DRIVE###################################################################.     
    def loadDriveAPI(self): #DONE
        creds = None
        if os.path.exists(DRIVETOKEN):
            creds = Credentials.from_authorized_user_file(DRIVETOKEN, DRIVESCOPES)
        if not creds or not creds.valid:
            
            if creds and creds.expired and creds.refresh_token:
                #print('y')
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    OKEY, DRIVESCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(DRIVETOKEN, 'w') as token:
                token.write(creds.to_json())

        #creds = service_account.Credentials.from_service_account_file(KEY, scopes = DRIVESCOPES)
        driveAPI = build('drive', 'v3', credentials=creds)
        return driveAPI

    def fileSavetoDrive(self, sourcefileID = str):
        destinationID = '18Rb-Tm6eQUoEDwIvzw_2pg8ImWPorSoD' 
        sheet_metadata = {                #NOT self.sheetGetDate(sourcefileID)   
            'mimeType': 'application/vnd.google-apps.spreadsheet',
            }
        sheet = self.loadDriveAPI().files().copy(fileId = sourcefileID,  body=sheet_metadata, fields='id').execute()
        sheet2 = self.loadDriveAPI().files().update( fileId = sheet.get('id'), addParents = destinationID).execute()    #move to folder
        print (f'FILE ID SAVED TO DRIVE: %s' % sheet2.get('id'))
        self.sheetCopyPaste(sheet2.get('id'))

#BOT###################################################################
    async def on_ready(self):

        for guild in self.guilds:
                if guild.name == GUILD:
                    break
        print(f'{self.user} has connected to Discord!')
        print(
                f'{self.user} is connected to the following guild:\n'
                f'{guild.name}(id: {guild.id})'
        ) 
        self.updateWorkerList()
        self.loadCalendarAPI()
        self.loadDriveAPI()
        self.loadSheetsAPI()
        print('Ready to go')


    async def on_message(self, message):
        
        if message.author.id == self.user.id:
            return

        if message.content.startswith('!hello'):
            await message.reply('Hello!', mention_author=True)
        
        if message.content.startswith('!checkWorkerList'):
            await message.channel.send("Week 1:")
            await message.channel.send(self.WorkerList[0])   
            await message.channel.send("Week 2:")
            await message.channel.send(self.WorkerList[1])

        if message.content.startswith('!updateCalendar'):
            self.updateAllEvents()   

        if message.content.startswith('!check'):
            for i in range(2):
                    for worker in self.WorkerList[i]:           
                        print (self.getPersonalSchedule(worker, i))

        if message.content.startswith('!uploadSchedule'):
            if message.content != '!uploadSchedule':
                NewMessage = await message.channel.send("processing. . . ")
                ID= self.getIDfromURL(message.content)  # getID
                self.fileSavetoDrive(ID)                  #save to drive
                self.updateWorkerList()
                self.updateCalendarList()
                await NewMessage.edit(content ="still processing. . . sorry. . .")
                self.updateAllEvents()
                await NewMessage.edit(content ="Done!")
                date = self.sheetGetDate(self.OutputSheetID)
                await message.channel.send('Schedule updated!')
                await message.channel.send('currentschedule starts ' + date)
            else :
                await message.channel.send('Schedule?')  

        if message.content.startswith('!getSchedule'):
            date = self.sheetGetDate(self.OutputSheetID)
            await message.channel.send('Most Recent Schedule: ')
            calendar_list = self.loadCalendarAPI().calendarList().list().execute()
            calendarsList = calendar_list['items']
            for calendar in calendarsList:
                if calendar['summary'].startswith('Alley'):
                    title = calendar['summary'] +'\n' +self.getURLfromCalendarID(calendar['id'])
                    await message.channel.send(title )
        
        if message.content.startswith('!status'):
            await message.channel.send('still alive, I guess')
        
        



#OTHER###########################

    def getIDfromURL(self, URL = str): #done    #only works for spreadsheet urls 
        start = URL.find('/d/')
        end = URL.find('/edit')
        ID = URL[start+3:end]     
        print(ID) 
        return ID  
    def getURLfromCalendarID(self, ID = str):
        URL = 'https://calendar.google.com/calendar/u/0?cid='+ ID
        return URL


client = MyClient()
client.run(TOKEN)