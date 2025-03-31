from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, lit, character_length
from pyspark.sql.types import StringType, IntegerType, DoubleType, LongType
import pyModeS as pms
import pyModeS.decoder.bds.bds60 as bds60
import base64

#### EL CODIGO DEL PREPROCESADO TRADUCIDO A SPARK
#### NO USA LIBRERIAS PARA PODER EJECUTARLO EN EL CLUSTER

# Definimos las funciones (antes esto iba dentro de las librerías)
def base64toHEX(b64):
    return base64.b64decode(b64).hex()

def getDownlink(hex):
    return pms.df(hex)

def getTypeCode(hex):
    return pms.common.typecode(hex)

def getICAO(hex):
    return str(pms.common.icao(hex))

def msgIsCorrupted(hex):
    return (pms.crc(hex) != 0)

def getOnGround(hex):
    decimal_value =  pms.bin2int(pms.hex2bin(hex)[5:8]) 
    if decimal_value == 4:
        return 1
    elif decimal_value == 5:
        return 0
    else:
        return None

class AircraftIdentificationMessage():

    def __init__(self):
        # DICCIONARIO DE COMBINACIONES PARA VARIABLE VORTEX,PRIMER NIVEL CAT, SEGUNDO NIVEL TC
        self.vortexDictionary = {
            1: {
                0: "No category information",
                1: "Reserved",
                2: "Reserved",
                3: "Reserved",
                4: "Reserved",
                5: "Reserved",
                6: "Reserved",
                7: "Reserved"
            },
            2: {
                0: "No category information",
                1: "Surface emergency vehicle",
                2: "ERROR",
                3: "Surface service vehicle",
                4: "Ground obstruction",
                5: "Ground obstruction",
                6: "Ground obstruction",
                7: "Ground obstruction"
            },
            3: {
                0: "No category information",
                1: "	Glider, sailplane",
                2: "Lighter-than-air",
                3: "Parachutist, skydiver",
                4: "Ultralight, hang-glider, paraglider",
                5: "Reserved",
                6: "Unmanned aerial vehicle",
                7: "Space or transatmospheric vehicle"
            },
            4: {
                0: "No category information",
                1: "Light (less than 7000 kg)",
                2: "Medium 1 (between 7000 kg and 34000 kg)",
                3: "Medium 2 (between 34000 kg to 136000 kg)",
                4: "High vortex aircraft",
                5: "Heavy (larger than 136000 kg)",
                6: "High performance (>5 g acceleration) and high speed (>400 kt)",
                7: "Rotorcraft"
            }
        }

    def match(self, typecode):
        return typecode >= 1 and typecode <= 4
    

    def getCA(self, hex):
        tc = self.getTypeCode(hex)
        # Asegurar que tc no es None antes de comparar
        if tc is None or not (1 <= tc <= 4):
            return None
        try:
            return pms.decoder.adsb.category(hex)
        except Exception:
            return None


    def getAircraftType(self, hex):
        tc = self.getTypeCode(hex)
        ca = self.getCA(hex)

        if tc in self.vortexDictionary and ca in self.vortexDictionary[tc]:
            return self.vortexDictionary[tc][ca]
        return None
    
    def updateRowFromHex(self, row, hex):
        callsign = pms.decoder.adsb.callsign(hex)
        tc = self.getTypeCode(hex)
        cat = pms.decoder.adsb.category(hex)
        row["callsign"] = callsign
        row["vortex"] = self.vortexDictionary[tc][cat]

    
    def getTypeCode(self, hex):
        return pms.common.typecode(hex)

# Wrappers para que sean funciones spark (User Defined Function)

base64toHEX_udf = udf(base64toHEX,StringType())
getDownlink_udf = udf(getDownlink, IntegerType())
getICAO_udf = udf(getICAO, StringType())
getOnGround_udf = udf(getOnGround, IntegerType())
getTypeCode_udf = udf(getTypeCode, IntegerType())
getHeading_udf = udf(bds60.hdg60, DoubleType())
getVerticalRate_udf = udf(bds60.vr60ins, IntegerType())
getAircraftType_udf = udf(AircraftIdentificationMessage().getAircraftType, StringType())
spark = SparkSession.builder.appName("procesadillo").getOrCreate()
#spark.sparkContext.setLogLevel("ERROR")

df = spark.read.options(delimiter=";", header=True).csv("test.csv")
df = df.withColumn("ts_kafka",col("ts_kafka").cast(LongType()))
df = df.drop("_c2") # se llama diferente en pyspark
print(df.dtypes)

df = df.withColumn("messageHex", base64toHEX_udf(col("message")))
df = df.withColumn("DL", getDownlink_udf(col("messageHex")))
df = df.withColumn("ICAO", getICAO_udf(col("messageHex")))
df = df.withColumn("timestamp", (col("ts_kafka") / 1000).cast("timestamp"))
df = df.withColumn("messageLen", character_length(col("messageHex")))

df_17_18 = df.filter(col("DL").isin([17, 18]) & (col("messageLen") == 28))
df_20_21 = df.filter(col("DL").isin([20, 21]) & (col("messageLen") == 28))


df_17_18 = df_17_18.withColumn("OnGround", getOnGround_udf(col("messageHex")))\
    .withColumn("TC", getTypeCode_udf(col("messageHex")))\
    .withColumn("AircraftType", getAircraftType_udf(col("messageHex")))

df_20_21 = df_20_21.withColumn("heading", getHeading_udf(col("messageHex")))\
    .withColumn("vertical_rate", getVerticalRate_udf(col("messageHex")))

## Añadimos columnas vacías para poder juntar los dfs
df_17_18 = df_17_18.withColumn('heading', lit(None).cast(DoubleType()))\
    .withColumn('vertical_rate', lit(None).cast(DoubleType()))

df_20_21 = df_20_21.withColumn('OnGround', lit(None).cast(IntegerType()))\
    .withColumn('TC', lit(None).cast(IntegerType()))\
    .withColumn('AircraftType', lit(None).cast(StringType()))

df_merged_ini = df_17_18.unionByName(df_20_21).orderBy(col("timestamp").asc())
df_merged_ini.repartition(1).write.mode("overwrite").csv("datos_prueba_sp.csv", header=True)

# prueba (da error si no haces .cache())
#df_20_21 = df_20_21.cache()
#df_20_21.filter(col("vertical_rate").isNotNull()).show(5)