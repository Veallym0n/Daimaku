import pymysql
conn = pymysql.connect()

class sampleClass(object):

    def __init__(self, *args, **kwargs):
        self.whatever = kwargs.get('author','kEvin1986')

    @staticmethod
    def get_data(self, username):
        cur = conn.cursor()
        cur.execute('select * from sampleTable where username="%s"' % self.whatever)
        data = cur.fetchall()
        cur.close()
        conn.close()
        print data
