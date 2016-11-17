### Flask settings
PORT = 9001
DEBUG = True

### MongoDB settings
MONGO_PORT = 57487

MONGO_PW = "csrocks1"
MONGO_USER = "407-Admin"
MONGO_URL = "mongodb://{}:{}@ds157487.mlab.com:57487/uo-club-manager".format(MONGO_USER, MONGO_PW)
