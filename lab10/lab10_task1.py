from collections import defaultdict
from datetime import datetime
import pytz
import requests

URL = 'https://collector-otp-prod.camsys-apps.com/realtime/gtfsrt/ALL/alerts?type=json&apikey=qeqy84JE7hUKfaI0Lxm2Ttcm6ZA0bYrP' 

class MTAFeed:
    '''
    This class fetches data from the MTA feed and parse them into active alerts
    based on the current time (or a time that it gives). The class should also
    act as a "dict" allowing user to iterate and retrieve items, with a special
    key 'Non Active Alerts' to list lines that have no active alerts.
    Sample usage:

    >>> feed = MTAFeed()

    >>> print(feed.getLines())
    {'1', '2', '3', '4', '5', '6', '7', 'A', 'B', 'C',..., 'SI', 'SF', 'SR'}

    >>> for item in feed.items():
    ...     print(item)
    ('Delays', {'N', 'W'})
    ('Planned - Express to Local', {'Z', 'J'})
    ('Planned - Trains Rerouted', {'D'})
    ('Station Notice', {'Z', 'J'})

    >>> feed.refresh()
    >>> for item in feed.items(include_non_active=True):
    ...     print(item)
    ('Delays', {'N', 'W'})
    ('Non Active Alerts', {'1', 'C', '2', '5', 'G', ..., 'Q'})
    ('Planned - Express to Local', {'Z', 'J'})
    ('Planned - Trains Rerouted', {'D'})
    ('Station Notice', {'Z', 'J'})

    >>> print(feed['Non Active Alerts'])
    {'1', 'C', '2', '5', 'G', ..., 'Q'}

    '''

    #URL = 'https://collector-otp-prod.camsys-apps.com/realtime/gtfsrt/ALL/alerts?type=json&apikey=qeqy84JE7hUKfaI0Lxm2Ttcm6ZA0bYrP' 

    def __init__(self):
        '''
        Initialize the class attributes and start retrieving the feed (by
        calling the class method self.refresh())
        '''
        self.timeZone = pytz.timezone('US/Eastern')
        self.refresh()
        self.data = requests.get(URL).json()
        self.lines = {'1','2','3','4','5','6','7','A','B','C','D','E','F','G','L','J','Z','N','M','Q','R','W','S','SI','SF','SR'}


    def refresh(self):
        '''
        This method refresh the data by downloading the feed, and extract the 
        alert based on the current timestamp (which is needed for checking
        active periods).
        '''
        self.__refresh_time = datetime.now().astimezone(self.timeZone)


    def getRefreshTime(self):
        '''
        This returns the datetime object of when we last refresh the feed. The
        datetime object should be timezone aware and in the same time zone of 
        the feed, 'US/Eastern'

        >>> feed.getRefreshTime().isoformat()
        '2023-03-29T09:00:28.789415-04:00'

        '''
        return self.__refresh_time

    def items(self, include_non_active=False):
        '''
        Returns an iterator to all alerts (including 'Non Active Alerts' if
        include_non_active is set to True). This should be a generator. The
        idea is to allow users to iterate through the alerts, e.g.:

        >>> for item in feed.items():
        ...
        '''
        # get all the alert types and lines out of the data
        self.data.keys()

        if(include_non_active):
            alerts = []
            for entity in self.data['entity']:
                for informed_entity in entity['alert']['informed_entity']:
                    if informed_entity.get('agency_id') == 'MTASBWY':
                        alertType = entity['alert']['transit_realtime.mercury_alert']['alert_type']
                        routeId = informed_entity.get('route_id')
                        if routeId:
                            alerts.append((alertType, routeId))
            result = {}
            for key, value in alerts:
                result.setdefault(key, set()).add(value)
                
            result = [(k, tuple(v)) for k, v in result.items()]
            return result
            #return set(alerts)
        else:
            entities = []
            for entity in self.data['entity']:
                for informed_entity in entity['alert']['informed_entity']:
                    ## get current time information
                    t = datetime.now().astimezone(pytz.timezone('US/Eastern'))
                    timeNow = t.timestamp()

                    ## go through entire list and determine if alert is active
                    for i in entity['alert']['active_period']:
                        # check if start time starts before our current time
                        if i.get('start') < timeNow: 
                            route_id = None
                            # there is no end time
                            if i.get('end', 'NA') == 'NA':
                                # make sure it is a subway
                                if informed_entity.get('agency_id') == 'MTASBWY': 
                                    alert_type = entity['alert']['transit_realtime.mercury_alert']['alert_type']
                                    route_id = informed_entity.get('route_id')
                            # there is an end time, check if it ends after our current time
                            elif i.get('end') > timeNow:
                                # make sure it is a subway
                                if informed_entity.get('agency_id') == 'MTASBWY': 
                                    alert_type = entity['alert']['transit_realtime.mercury_alert']['alert_type']
                                    route_id = informed_entity.get('route_id')
                            
                            # if route_id is not None
                            if route_id and route_id in self.lines:
                                entities.append((alert_type, route_id))
            result = {}
            for key, value in entities:
                result.setdefault(key, set()).add(value)
                
            result = [(k, tuple(v)) for k, v in result.items()]
            return result
            #return set(entities)

    def __getitem__(self, alert_type):
        '''
        We override this built-in operator to allow users to directly retrieve
        the set of lines associated with the alert_type, e.g.:

        >>> print(feed['Delays'])
        {'N', 'W'}

        '''
        self.data.keys()
        alertLines = {'1','2','3','4','5','6','7','A','B','C','D','E','F','G','L','J','Z','N','M','Q','R','W','S', 'SI', 'SF', 'SR'}

        if(alert_type == 'Non Active Alerts'):
            for entity in self.data['entity']:
                for informed_entity in entity['alert']['informed_entity']:
                    # get current time information
                    t = datetime.now().astimezone(pytz.timezone('US/Eastern'))
                    timeNow = t.timestamp()

                    # go through entire list and determine if alert is active
                    for i in entity['alert']['active_period']:
                        # check if start time starts before our current time
                        if i.get('start') < timeNow: 
                            route_id = None
                            # there is no end time
                            if i.get('end', 'NA') == 'NA':
                                # make sure it is a subway
                                if informed_entity.get('agency_id') == 'MTASBWY': 
                                    route_id = informed_entity.get('route_id')
                            # there is an end time, check if it ends after our current time
                            elif i.get('end') > timeNow:
                                # make sure it is a subway
                                if informed_entity.get('agency_id') == 'MTASBWY': 
                                    route_id = informed_entity.get('route_id')
                            
                            if route_id in alertLines: #route_id and (route_id in lines):
                                alertLines.remove(route_id)    
        else:
            for entity in self.data['entity']:
                for informed_entity in entity['alert']['informed_entity']:
                    if informed_entity.get('agency_id') == 'MTASBWY':
                        currAlert = entity['alert']['transit_realtime.mercury_alert']['alert_type']
                        if(currAlert in alertLines):
                            alertLines.remove(currAlert)          
        return alertLines 

    def getLines(self):
        '''
        Return the set of all possible lines
        '''
        return self.lines 
        

if __name__ == '__main__':
    feed = MTAFeed()
    print('Last refresh: ', feed.getRefreshTime().isoformat(' ')[:19])
    for status, lines in feed.items():
        print(status, ':', ' '.join(sorted(lines)))
    no_active = 'Non Active Alerts'
    print(no_active, ':', ' '.join(sorted(feed[no_active])))