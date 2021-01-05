#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 导入WorkWeixinRobot 库
from WorkWeixinRobot.work_weixin_robot import WWXRobot
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, date, timedelta
import requests
import time
import sys

WXROBOTKEY = '0aec9772-9770-46ac-9a17-04bb58a18e5e'
HEFENGAPI = 'https://devapi.qweather.com/v7/weather/now?'
HEFENGKEY = '81ab769e12c743348b233a2f45bdceec'
HOLIDAYAPI = 'http://v.juhe.cn/calendar/month?'
CALENDARAPI = 'http://v.juhe.cn/calendar/day?'
CALENDARKEY = 'cd8e2e0e6ef1c5374bedc6f837b46430'


rbt = WWXRobot(key=WXROBOTKEY)

# 发送一个字符串作为文本消息
# rbt.send_text(content='表情')

# msg = {
#     "msgtype": "text",
#     "text": {
#         "content": "广州今日天气：29度，大部分多云，降雨概率：60%",
#         "mentioned_list":["101009668","@all"],
#         "mentioned_mobile_list":["13627903282"]
#     }
# }
# msg = {
#     "msgtype": "text",
#     "text": {
#         "content": "广州今日天气：29度，大部分多云，降雨概率：60%",
#         "mentioned_list":["101009668","@all"],
#         "mentioned_mobile_list":["13627903282"]
#     }
# }
# rbt._send(body=msg)

workingDaySet = set()
# festivalSet = set()

def log(tag, **kw):
    t = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    print(t+'   ', tag + "   :   ", "info:", kw)


def formatCalendarDay(dayStr):
    res = dayStr
    if( len(dayStr.split('-')[1])==1 ):
        res = res[:5] + '0' + res[5:]
    if( len(dayStr.split('-')[2])==1 ):
        res = res[:8] + '0' + res[8:]
    return res

def remindaHoliday(holidayInfo):
    msg = '今天是' + holidayInfo + '，二狗祝您' + holidayInfo + '快乐！'
    rbt.send_text(content=msg)

def updateWorkingDay():
    today = time.strftime('%Y-%m')
    if( today[-2]=='0' ):
        today = today[:-2] + today[-1:]
    recentHolidayRes = requests.get(HOLIDAYAPI + 'year-month=' + today + '&key=' + CALENDARKEY)
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
    calendarRes = requests.get(CALENDARAPI + 'date=' + today + '&key=' + CALENDARKEY)
    if( recentHolidayRes.json()['reason']=='Success' ):
        holidayInfo = recentHolidayRes.json()['result']['data']['holiday']
        if( holidayInfo!='' ):
            log(sys._getframe().f_code.co_name, holiday=holidayInfo)
            remindaHoliday(holidayInfo)

def weatherInfoFormat(resJson):
    weather = ''
    needUmbrella = False
    if ( resJson['text']=='晴' ):
        weather = resJson['text'] + '☀'
    elif( resJson['text']=='多云' ):
        weather = resJson['text'] + '⛅'
    elif( resJson['text']=='阴' ):
        weather = resJson['text'] + '☁'
    elif( '雨' in resJson['text'] ):
        needUmbrella = True
        weather = resJson['text'] + '🌧'
    elif( resJson['text']=='雾' ):
        weather = resJson['text'] + '🌫'
    elif( resJson['text']=='霾' ):
        weather = resJson['text'] + '🌫🌫'
    else:
        weather = resJson['text']
    msg = weather + '\n空气温度:' + resJson['temp'] + '°C\n体表温度：' + resJson['feelsLike'] + '°C\n' + resJson['windDir'] + resJson['windScale'] + '级，相对湿度：' + resJson['humidity'] + '%。'
    if( needUmbrella ):
        msg + '\n今天可能会下雨，出门记得带伞哦！'
    return msg

def weatherInfo():
    shanghaiWeather = ''
    wuxiWeather = ''
    shanghaiResponse = requests.get(HEFENGAPI + 'location=101020100&key=' + HEFENGKEY)
    if( shanghaiResponse.json()['code']=='200' ):
        shanghaiResponseNow = shanghaiResponse.json()['now']
        shanghaiWeather = '当前上海市天气状况为：\n' +  weatherInfoFormat(shanghaiResponseNow)
    wuxiWeatherResponse = requests.get(HEFENGAPI + 'location=101190201&key=' + HEFENGKEY)
    if( wuxiWeatherResponse.json()['code']=='200' ):
        wuxiResponseNow = wuxiWeatherResponse.json()['now']
        wuxiWeather = '当前无锡市天气状况为：\n' +  weatherInfoFormat(wuxiResponseNow)
    return shanghaiWeather + '\n\n' + wuxiWeather

def sendWeatherMsg():
    log(sys._getframe().f_code.co_name)
    weatherMsg = weatherInfo()
    # print(weatherMsg)
    rbt.send_text(content=weatherMsg)

def alarmRemind():
    log(sys._getframe().f_code.co_name)
    tomorrow = (date.today() + timedelta(days= 1)).strftime("%Y-%m-%d")
    if( tomorrow in workingDaySet ):
        rbt.send_text(content='明天也是工作日，记得定闹钟不要迟到哦！')

def main():
    updateWorkingDay()
    sched = BlockingScheduler()
    sched.add_job(sendWeatherMsg, 'cron', day_of_week='*', hour=8, minute=0)
    sched.add_job(getCalendarInfo, 'cron', day_of_week='*', hour=9, minute=0)
    sched.add_job(alarmRemind, 'cron', day_of_week='*', hour=20, minute=0)
    sched.add_job(updateWorkingDay, 'cron', month='*', day=1, hour=0, minute=0)
    sched.start()

if __name__=="__main__":
    main()