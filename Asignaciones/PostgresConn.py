from pandas import read_sql, DataFrame
import pandas as pd
import psycopg2

class Database:
    """PostgreSQL Database class.For the Asignaciones APP"""

    def __init__(self, data):
        self.host = data["BonnysaDB"]["host"]
        self.username = data["BonnysaDB"]["username"]
        self.password = data["BonnysaDB"]["password"]
        self.port = data["BonnysaDB"]["port"]
        self.dbname = data["BonnysaDB"]["dbname"]
        self.conn = psycopg2.connect(host=self.host,port=self.port,user=self.username,password=self.password,dbname=self.dbname)
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def selectall(self, sele, tablename, type):
        query = """
                SELECT {}
                FROM public.{};
                """.format(sele, tablename)
              
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def read(self,query, type):
        self.cursor.execute(query) 

        records = [row for row in self.cursor.fetchall()]
        
        if not records:
            values =  [0] * len([ x.name for x in self.cursor.description ])
            heads = [ x.name for x in self.cursor.description ]
            dictionary = dict(zip(heads, values))

            df =pd.DataFrame.from_dict(dictionary, orient='index')
            df = df.T

        else:
            df = pd.DataFrame(records)
            df.columns=[ x.name for x in self.cursor.description ]
        
        #self.cursor.close()

        records = df.to_records(index=False)
            #print(records)
        tup = list(records)

        if type == "dataframe":
            return df
        if type == "tuple":
            return tup

    def eval(self, df, type):
        #if df.empty:
            #df =  pd.DataFrame({0 : [0]})
            #tup = []

        if type == "dataframe":
            return df
        if type == "tuple":
            records = df.to_records(index=False)
            tup = list(records)
            return tup

    def insert(self,tablename,var,value):
        query = """
                INSERT INTO public.{} {}              
                VALUES {};
                """.format(tablename,var,value)        
        self.cursor.execute(query)
        self.conn.commit()

    def modifyManual(self, tablename, asig, idvalue):
        query = """
                UPDATE public.{}
                SET {}              
                WHERE id = {};
                """.format(tablename,asig,idvalue)       
        self.cursor.execute(query)
        self.conn.commit()    

    def select_orders(self, rang):
        query = "SELECT *, coalesce((SELECT concat('LN', CAST (linea_id AS VARCHAR))  FROM public.ofs where id_pedido = pedidosllanos.id limit 1), ' ') as linea FROM public.pedidosllanos WHERE fecha_carga >= current_date - interval '{}' day AND fecha_carga < current_date + interval '{}' day and estado IN ('1', '5');".format(rang, rang)
        df = read_sql(query, self.conn)
        return df

    def select_ofs_by_date(self,rang):
        query = "SELECT * FROM public.ofs WHERE fecha_carga >= current_date - interval '{}' day AND fecha_carga < current_date + interval '{}' day;".format(rang, rang)
        df = read_sql(query, self.conn)
        return df
    
    def select_ofs(self):
        query = "SELECT * FROM public.ofs;"
        df = read_sql(query, self.conn)
        return df

    def select_of_by_id(self, idof):
        query = "SELECT * FROM public.ofs where id = '{}';".format(idof)
        df = read_sql(query, self.conn)
        return df

    def select_ofs_by_idpedido(self, idpedido):
        query = "SELECT * FROM public.ofs where id_pedido = '{}';".format(idpedido)
        df = read_sql(query, self.conn)
        return df

    def select_pedido_by_id(self, idpedido):
        query = "SELECT * FROM public.pedidosllanos where id = '{}';".format(idpedido)
        df = read_sql(query, self.conn)
        return df

    def select_old_pallets(self, idpedido):
        query = "SELECT * FROM public.pedidosllanos where id = '{}';".format(idpedido)
        df = read_sql(query, self.conn)
        return df

    def select_devices(self):
        query = "SELECT * FROM public.devices;"
        df = read_sql(query, self.conn)
        return df

    def select_linea_incidencia_by_id(self, id):
        query = "SELECT * FROM public.linea_incidencia where id_device = '{}';".format(id)
        df = read_sql(query, self.conn)
        return df

    def select_standar_events(self):
        query = "SELECT * FROM public.standarevents;"
        df = read_sql(query, self.conn)
        return df

    def insert(self,tablename,var,value):
        query = """
                INSERT INTO public.{} {}              
                VALUES {};
                """.format(tablename,var,value)

        self.cursor.execute(query)
        self.conn.commit()

    def insert_r(self,tablename,var,value):
        query = """
                INSERT INTO public.{} {}              
                VALUES {} RETURNING id;
                """.format(tablename,var,value)

        self.cursor.execute(query)
        records = self.cursor.fetchall()
        self.conn.commit()
        return records

    def delete(self,tablename,id):
        query = """
                DELETE FROM public.{}
                WHERE id = {}
                """.format(tablename,id)

        self.cursor.execute(query)
        self.conn.commit()

    def modify(self,tablename,column,value,idvalue):
        query = """
                UPDATE public.{}
                SET {} = '{}'              
                WHERE id = {};
                """.format(tablename,column,value,idvalue)

        self.cursor.execute(query)
        self.conn.commit()

    def select_max_orden(self):
        query = "SELECT max(orden) orden FROM public.ofs;"
        df = read_sql(query, self.conn)
        return df

    def select(self, sele, tablename, var, value, type):
        query = """
                SELECT {}
                FROM public.{}
                WHERE {} = {};
                """.format(sele, tablename, var, value)        
        df = read_sql(query, self.conn)
        return df
    

if __name__ == "__main__":
    sql = Database()
    print("Conectado a la base de datos, con IP: " + sql.host + "Usamos la tabla: "+ sql.dbname)
