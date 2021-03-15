import numpy as np
import xlrd
from chinese_calendar import is_workday
from WorkWeixinRobot.work_weixin_robot import WWXRobot
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import datetime
import requests
import time
import sys


# 测试# 0aec9772-9770-46ac-9a17-04bb58a18e5e
# 工程组# 6a6f908b-58a4-4757-b439-3bdfc2fc17d9
WXROBOTKEY = '0aec9772-9770-46ac-9a17-04bb58a18e5e'
HEFENGNOWAPI = 'https://devapi.qweather.com/v7/weather/now?'
HEFENGTHREEDAYAPI = 'https://devapi.qweather.com/v7/weather/3d?'
HEFENGKEY = '81ab769e12c743348b233a2f45bdceec'
HOLIDAYAPI = 'http://v.juhe.cn/calendar/month?'
CALENDARAPI = 'http://v.juhe.cn/calendar/day?'
CALENDARKEY = 'cd8e2e0e6ef1c5374bedc6f837b46430'

rbt = WWXRobot(key=WXROBOTKEY)
sched = BlockingScheduler()
workingDaySet = set()
GShanghaiWeather = '上海市实时天气状况：'
GWuxiWeather = '无锡市实时天气状况：'
GWeatherUpdated = False


def log(tag, **kw):
    t = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    if( len(kw) > 0 ):
        print('%-25s%-20s:  %s' % (t, tag, kw))
    else:
        print('%-25s%-20s:' % (t, tag))

class Employee(object):
    def __init__(self, date, name, id, status, workingDay, dayOff, sumDays):
        self.__date = date
        self.__name = name
        self.__id = id
        self.__status = status
        self.__workingDay = workingDay
        self.__dayOff = dayOff
        self.__sumDays = sumDays
    def getId(self):
        return self.__id
    def getName(self):
        return self.__name
    def getDate(self):
        return self.__date
    def getStatus(self):
        return self.__status
    def getWorkingDay(self):
        return self.__workingDay
    def getDayOff(self):
        return self.__dayOff
    def getSumDays(self):
        return self.__sumDays

def formatCalendarDay(dayStr):
    res = dayStr
    if( len(dayStr.split('-')[1])==1 ):
        res = res[:5] + '0' + res[5:]
    if( len(dayStr.split('-')[2])==1 ):
        res = res[:8] + '0' + res[8:]
    return res

def isRunYear(year):
	if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
		return True
	else:
		return False

def workingDayOfMonth(date):
	daysOfMonth = [31,28,31,30,31,30,31,31,30,31,30,31]
	daysInLastMonth = 0
	today = datetime.datetime.now().date()
	workingDayCnt = 0
	if (int(date.split('-')[0]) == today.year and int(date.split('-')[1]) == today.month):	#同月
		for i in range(1, today.day):
			monthDate = datetime.date(today.year, today.month, i)
			if is_workday(monthDate):
				workingDayCnt += 1
	else:
		if( int(date.split('-')[1])==2 and isRunYear(int(date.split('-')[0])) ):
			daysInLastMonth = 29
		else:
			daysInLastMonth = daysOfMonth[int(date.split('-')[1])-1]
		print("daysInLastMonth",daysInLastMonth," int(date.split('-')[1])-1", int(date.split('-')[1])-1, " ,date=" + date)
		print("\nint(date.split('-')[0])",int(date.split('-')[0])," iint(date.split('-')[1])", int(date.split('-')[1]))
		for i in range(1, daysInLastMonth+1):
			monthDate = datetime.date(int(date.split('-')[0]), int(date.split('-')[1]), i)
			if is_workday(monthDate):
				workingDayCnt += 1
	return workingDayCnt

def remindaHoliday(holidayInfo):
    msg = '今天是' + holidayInfo + '，祝大家' + holidayInfo + '快乐！'
    rbt.send_text(content=msg)

def updateWorkingDay():
    today = time.strftime('%Y-%m')
    if( today[-2]=='0' ):
        today = today[:-2] + today[-1:]
    url = HOLIDAYAPI + 'year-month=' + today + '&key=' + CALENDARKEY
    log(sys._getframe().f_code.co_name, url=url)
    recentHolidayRes = requests.get(url)
    if( recentHolidayRes.json()['reason']=='Success' ):
        holidayArray = recentHolidayRes.json()['result']['data']['holiday_array']
        for hol in holidayArray:
            # festivalSet.add(formatCalendarDay(hol['festival']))
            festHolidayList = hol['list']
            for fest in festHolidayList:
                if( fest['status']=='2' ):
                    workingDaySet.add(formatCalendarDay(fest['date']))
    # log(sys._getframe().f_code.co_name, festivalSet=sorted(festivalSet), workingDaySet=sorted(workingDaySet))
    log(sys._getframe().f_code.co_name, workingDaySet=sorted(workingDaySet))

def getCalendarInfo():
    log(sys._getframe().f_code.co_name)
    today = time.strftime('%Y-%m-%d')
    if( today[-5]=='0' ):
        today = today[:-5] + today[-4:]
    if( today[-2]=='0' ):
        today = today[:-2] + today[-1:]
    url = CALENDARAPI + 'date=' + today + '&key=' + CALENDARKEY
    log(sys._getframe().f_code.co_name, url=url)
    calendarRes = requests.get(url)
    if( calendarRes.json()['reason']=='Success' ):
        try:
            holidayInfo = calendarRes.json()['result']['data']['holiday']
            if( holidayInfo!='' ):
                log(sys._getframe().f_code.co_name, holiday=holidayInfo)
                remindaHoliday(holidayInfo)
        except KeyError:
            log(sys._getframe().f_code.co_name, date=today, error=KeyError)

def addWeatherIcon(weatherText):
    weather = ''
    if ( weatherText=='晴' ):
        weather = weatherText + '☀'
    elif( weatherText=='多云' ):
        weather = weatherText + '⛅'
    elif( weatherText=='阴' ):
        weather = weatherText + '☁'
    elif( ('雨' in weatherText) and ('雪' not in weatherText) ):
        weather = weatherText + '🌧'
    elif( weatherText=='雾' ):
        weather = weatherText + '🌫'
    elif( weatherText=='霾' ):
        weather = weatherText + '🌫🌫'
    elif( '雪' in weatherText ):
        weather = weatherText + '❄'
    else:
        weather = weatherText
    return weather

def weatherTodayInfoFormat(resJson):
    weather = ''
    needUmbrella = False
    weatherOfToday = resJson[0]
    textDay = weatherOfToday['textDay']
    textNight = weatherOfToday['textNight']
    tempMax = weatherOfToday['tempMax']
    tempMin = weatherOfToday['tempMin']
    windDirDay = weatherOfToday['windDirDay']
    windScaleDay = weatherOfToday['windScaleDay']
    humidity = weatherOfToday['humidity']
    if( ('雨' in textDay) or ('雨' in textNight) ):
        needUmbrella = True
    daySummary = ''
    if( textDay != textNight ):
        daySummary = addWeatherIcon(textDay) + '转' + addWeatherIcon(textNight) + '\n'
    else:
        daySummary = addWeatherIcon(textDay)
    dayTemp = '温度：' + tempMin + '°C ~ ' + tempMax + '°C\n'
    dayWindAndHumidity = windDirDay + windScaleDay + '级， 相对湿度：' + humidity + '%\n'
    msg = '全天：\n' + daySummary + dayTemp + dayWindAndHumidity
    if( needUmbrella ):
        msg = msg + '今天可能会下雨，出门记得带伞☔哦！'
    return msg

def weatherInfo():
    log(sys._getframe().f_code.co_name)
    global GShanghaiWeather
    global GWuxiWeather
    global GWeatherUpdated
    GShanghaiWeather = '上海市实时天气状况：'
    GWuxiWeather = '无锡市实时天气状况：'
    shanghaiNowWeather = ''
    wuxiNowWeather = ''
    shanghaiTodayWeather = ''
    wuxiTodayWeather = ''
    shCityId = '101020100'
    wxCityId = '101190201'
    shNowUrl = HEFENGNOWAPI + 'location=' + shCityId + '&key=' + HEFENGKEY
    shanghaiWeatherNowRes = requests.get(shNowUrl)
    shThreedayUrl = HEFENGTHREEDAYAPI + 'location=' + shCityId + '&key=' + HEFENGKEY
    shanghaiWeatherThreedayRes = requests.get(shThreedayUrl)
    log(sys._getframe().f_code.co_name, shNowUrl=shNowUrl, shThreedayUrl=shThreedayUrl)
    if( shanghaiWeatherNowRes.json()['code']=='200' ):
        shanghaiResponseNow = shanghaiWeatherNowRes.json()['now']
        shanghaiNowWeather = addWeatherIcon(shanghaiResponseNow['text']) + '\n'
    if( shanghaiWeatherThreedayRes.json()['code']=='200' ):
        shanghaiResponseDaily = shanghaiWeatherThreedayRes.json()['daily']
        shanghaiTodayWeather = weatherTodayInfoFormat(shanghaiResponseDaily)
    GShanghaiWeather = GShanghaiWeather + shanghaiNowWeather + shanghaiTodayWeather
    log(sys._getframe().f_code.co_name, GShanghaiWeather=GShanghaiWeather)

    wxNowUrl = HEFENGNOWAPI + 'location=' + wxCityId + '&key=' + HEFENGKEY
    wuxiWeatherNowRes = requests.get(wxNowUrl)
    wxThreedayUrl = HEFENGTHREEDAYAPI + 'location=' + wxCityId + '&key=' + HEFENGKEY
    wuxiWeatherThreedayRes = requests.get(wxThreedayUrl)
    log(sys._getframe().f_code.co_name, wxNowUrl=wxNowUrl, wxThreedayUrl=wxThreedayUrl)
    if( wuxiWeatherNowRes.json()['code']=='200' ):
        wuxiResponseNow = wuxiWeatherNowRes.json()['now']
        wuxiNowWeather = addWeatherIcon(wuxiResponseNow['text']) + '\n'
    if( wuxiWeatherThreedayRes.json()['code']=='200' ):
        wuxiResponseDaily = wuxiWeatherThreedayRes.json()['daily']
        wuxiTodayWeather = weatherTodayInfoFormat(wuxiResponseDaily)
    GWuxiWeather = GWuxiWeather + wuxiNowWeather + wuxiTodayWeather
    GWeatherUpdated = True
    log(sys._getframe().f_code.co_name, GWuxiWeather=GWuxiWeather)
    return GShanghaiWeather + '\n\n' + GWuxiWeather

def sendWeatherMsg():
    log(sys._getframe().f_code.co_name)
    global GWeatherUpdated
    if GWeatherUpdated :
        weatherMsg = GShanghaiWeather + '\n\n' + GWuxiWeather
        rbt.send_text(content=weatherMsg)
    GWeatherUpdated = False

def alarmRemind():
    log(sys._getframe().f_code.co_name)
    tomorrow = (datetime.date.today() + datetime.timedelta(days= 1)).strftime("%Y-%m-%d")
    if( tomorrow in workingDaySet ):
        rbt.send_text(content='明天也是工作日，记得定闹钟不要迟到哦！')

def reportRemind():
    wb = xlrd.open_workbook("report.xlsx")
    sheet1 = wb.sheet_by_index(0)
    x = np.array([sheet1.nrows, sheet1.ncols], dtype=str)
    employeeList = []
    mentionedList = []
    mentionedMsg = []
    lackCnt = 0
    for rowNum in range(2, sheet1.nrows):
        rowVale = sheet1.row_values(rowNum)
        employeeList.append(Employee(xlrd.xldate_as_datetime(rowVale[1], 0).strftime('%Y-%m'), rowVale[3], rowVale[4], rowVale[5], rowVale[6], rowVale[7], rowVale[8]))
    for emp in employeeList:
    	# print("date=", emnp.getDate(), "id=", emp.getId(), " status=", emp.getStatus(), " workingDay=", emp.getWorkingDay(), " dayoff=", emp.getDayOff(), " sumDays=", emp.getSumDays(), "\n")
        if( emp.getWorkingDay() < workingDayOfMonth(emp.getDate()) and (not str(emp.getId()).startswith('WB'))):
            if( emp.getStatus()=='在职' ):
                lackCnt += 1
                mentionedList.append(str(int(emp.getId())))
                msg = str(emp.getName()) + ':' + str(int(emp.getWorkingDay())) + '天'
                mentionedMsg.append(msg)
    content = '，'.join(mentionedMsg)
    messageHead = str(lackCnt) + '人漏填日报，实际应填' + str(workingDayOfMonth(emp.getDate())) + '个工作日，请大家今日补齐漏填天数，不要产生罚款。\n\n'
    wechatMsg = {
        "msgtype": "text",
        "text": {
            "content": messageHead + content,
            "mentioned_list":mentionedList,
        }
    }
    print(wechatMsg)
    print("\nmentionedList=\n", mentionedList)
    print("\ncontent=\n", content)
    rbt._send(body=wechatMsg)

def job_listener(event):
    job = sched.get_job(event.job_id)
    args = job.args
    if not event.exception:
        log(sys._getframe().f_code.co_name, statu="SUCCESS", jobName=job.name)
    else:
        msg = "jobname={}|jobtrigger={}|errcode={}|exception=[{}]|traceback=[{}]|scheduled_time={}".format(job.name, job.trigger, event.code, event.exception, event.traceback, event.scheduled_run_time)
        log(sys._getframe().f_code.co_name, statu="FAIL",  msg=msg)
        next_datetime = datetime.datetime.now() + datetime.timedelta(seconds=5)
        sched.reschedule_job(event.job_id, trigger='cron', hour=next_datetime.hour, minute=next_datetime.minute, second=next_datetime.second)

def main():
    updateWorkingDay()
    sched.add_job(weatherInfo, 'cron', day_of_week='*', hour=7, minute=58)
    sched.add_job(sendWeatherMsg, 'cron', day_of_week='*', hour=8, minute=0)
    sched.add_job(getCalendarInfo, 'cron', day_of_week='*', hour=9, minute=0)
    sched.add_job(alarmRemind, 'cron', day_of_week='*', hour=20, minute=0)
    sched.add_job(updateWorkingDay, 'cron', month='*', day=1, hour=0, minute=0)
    sched.add_listener(job_listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)
    sched.start()

if __name__=="__main__":
    # reportRemind()
    # sendWeatherMsg()
    main()
