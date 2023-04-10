import cryptography
import random
from datetime import time
import json


def generateDayTimeTable(numberOfTimeMoments: int = 12, seed: int = 123):
    random.seed(seed)
    if (numberOfTimeMoments < 0):
        numberOfTimeMoments = 0

    setOfHours = set()
    timeMoments = dict()
    for i in range (0, numberOfTimeMoments):
        hour = random.randint(0, 23)
        while hour in setOfHours:
            hour = random.randint(0, 23)
        setOfHours.add(hour)
        minute = random.randint(0, 59)
        timeMoments[hour] = minute
    timeMoments["pause length"] = random.randint(15, 120)

    return timeMoments


def writeTimeTableToJson(numberOfTimeMoments: int = 12, seed: int = 123):
    timeMoments = generateDayTimeTable(numberOfTimeMoments, seed)

    with open("timeTable.json", "w") as json_file:
        json.dump(timeMoments, json_file)

if __name__ == '__main__':
    writeTimeTableToJson()