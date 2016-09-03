from starwars_api.client import SWAPIClient
from starwars_api.exceptions import SWAPIClientError
import re
api_client = SWAPIClient()


class BaseModel(object):

    def __init__(self, json_data):
        """
        Dynamically assign all attributes in `json_data` as instance
        attributes of the Model.
        """
        for key, value in json_data.items():
            setattr(self, key, value)
        
        

    @classmethod
    def get(cls, resource_id):
        """
        Returns an object of current Model requesting data to SWAPI using
        the api_client.
        """
        if cls.RESOURCE_NAME == 'people':
            return cls(api_client.get_people(resource_id))
        
        if cls.RESOURCE_NAME == 'films':
            return cls(api_client.get_films(resource_id))
        
        
    @classmethod
    def all(cls):
        """
        Returns an iterable QuerySet of current Model. The QuerySet will be
        later in charge of performing requests to SWAPI for each of the
        pages while looping.
        """
        if cls.RESOURCE_NAME == 'people':
            return PeopleQuerySet()
        
        if cls.RESOURCE_NAME == 'films':
            return FilmsQuerySet()


class People(BaseModel):
    """Representing a single person"""
    RESOURCE_NAME = 'people'

    def __init__(self, json_data):
        super(People, self).__init__(json_data)

        
    def __repr__(self):
        return 'Person: {0}'.format(self.name.encode('utf-8'))


class Films(BaseModel):
    RESOURCE_NAME = 'films'

    def __init__(self, json_data):
        super(Films, self).__init__(json_data)

    def __repr__(self):
        return 'Film: {0}'.format(self.title.encode('utf-8'))


class BaseQuerySet(object):
    
    def __init__(self):
        self.counter = 0 # Running counter of items returned
        self.api_call = getattr(api_client, 'get_{}'.format(self.r_name)) # Call API based on r_name varible
        self.iter_count = 0 # Iteration counter per page of JSON data
        self.page = 1 # Page to call in the API
        self.json_data = self.api_call("?page={}".format(self.page)) # API Call mapped to page returns JSON Data
        self.result_count = self.json_data['count'] # Count key value from the returned JSON Data
        
    def __iter__(self):
        return self

    def __next__(self):
        """
        Must handle requests to next pages in SWAPI when objects in the current
        page were all consumed.
        """
        # When total iterations match 'count' from JSON data stop iteration
        if self.counter == self.result_count:
            raise StopIteration
        # Try to pull out a single result set and return it as an obj base on return_func
        try:
            return_val = self.return_func(self.json_data['results'][self.iter_count])
            self.counter += 1
            self.iter_count += 1
            return return_val
        except IndexError:
            self.page = re.match(r'^.*page=(.*)', self.json_data['next']).group(1) # If index is past end of list update the page based of page listed in JSON data
            self.json_data = self.api_call("?page={}".format(self.page)) # Make new API call on new page
            self.counter += 1
            self.iter_count = 1 # Reset the iter counter
            return self.return_func(self.json_data['results'][0]) # Return first item from next page


    next = __next__

    def count(self):
        """
        Returns the total count of objects of current model.
        If the counter is not persisted as a QuerySet instance attr,
        a new request is performed to the API in order to get it.
        """
        return self.result_count


class PeopleQuerySet(BaseQuerySet):
    RESOURCE_NAME = 'people'

    def __init__(self):
        self.r_name = 'people'
        self.return_func = People
        super(PeopleQuerySet, self).__init__()
        
    def __repr__(self):
        return 'PeopleQuerySet: {0} objects'.format(str(self.count()))


class FilmsQuerySet(BaseQuerySet):
    RESOURCE_NAME = 'films'

    def __init__(self):
        self.r_name = 'films'
        self.return_func = Films
        super(FilmsQuerySet, self).__init__()

    def __repr__(self):
        return 'FilmsQuerySet: {0} objects'.format(str(self.count()))