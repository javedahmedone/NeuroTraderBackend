from datetime import datetime, timedelta
from app.global_constant import constants
import pytz

class CommonService:
    def __init(self):
        pass
    
    def currentIstTime(self):
        return datetime.now(pytz.timezone("Asia/Kolkata"))  
        
    def fetchFromDate(self, todayDate:datetime, interval: str):
        todayDate = datetime.strptime(todayDate, "%Y-%m-%d")
        day_of_week = todayDate.strftime("%A")
        if day_of_week == "Saturday" or day_of_week == "Sunday":
            todayDate -= timedelta(days=day_of_week == "Saturday" and 1 or 2)
        if interval == constants.ONEWEEK:
            result = todayDate - timedelta(days=7)
        elif interval == constants.ONEMONTH:
            result = todayDate - timedelta(days=30)
        elif interval == constants.THREEMONTH:
            result = todayDate - timedelta(days=90)
        elif interval == constants.ONEYEAR:
            result = todayDate - timedelta(days=365)
        elif interval == constants.FIVEYEAR:
            result = todayDate - timedelta(days=1825)
        elif interval == constants.ALL:
            return "2000-01-01 09:15"
        else:
            result = todayDate
        return result.strftime("%Y-%m-%d") + " 09:15"    
    
    def intervalTimeMapping(self, interval: str):
        if interval == constants.ONEWEEK:
            return "ONE_WEEK"
        elif interval == constants.ONEMONTH:
            return "ONE_DAY"
        elif interval == constants.THREEMONTH:
            return "ONE_DAY"
        elif interval == constants.ONEYEAR:
            return "ONE_DAY"   
        elif interval == constants.FIVEYEAR:
            return "ONE_DAY"
        elif interval == constants.ALL:
            return "ONE_DAY"
        else:
            return "ONE_MINUTE"
