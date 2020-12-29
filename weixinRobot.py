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
HEFENGNOWAPI = 'https://devapi.qweather.com/v7/weather/now?'
HEFENGTHREEDAYAPI = 'https://devapi.qweather.com/v7/weather/3d?'
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
    if( len(kw) > 0 ):
        print('%-25s%-20s:  %s' % (t, tag, kw))
    else:
        print('%-25s%-20s:' % (t, tag))


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
    shanghaiWeather = '上海市实时天气状况：'
    wuxiWeather = '无锡市实时天气状况：'
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
    shanghaiWeather = shanghaiWeather + shanghaiNowWeather + shanghaiTodayWeather
    log(sys._getframe().f_code.co_name, shanghaiWeather=shanghaiWeather)

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
    wuxiWeather = wuxiWeather + wuxiNowWeather + wuxiTodayWeather
    log(sys._getframe().f_code.co_name, wuxiWeather=wuxiWeather)
    return shanghaiWeather + '\n\n' + wuxiWeather

def sendWeatherMsg():
    log(sys._getframe().f_code.co_name)
    weatherMsg = weatherInfo()
    # rbt.send_text(content=weatherMsg)

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
    sendWeatherMsg()
    # main()