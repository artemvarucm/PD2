## **Resumen del capítulo "Airborne Velocity"**

Este capítulo del libro *The 1090 Megahertz Riddle* explica cómo se transmiten y decodifican los datos de velocidad de aeronaves en ADS-B.

---

### **Estructura del mensaje de velocidad en vuelo**
Los mensajes de velocidad en vuelo usan el **Type Code 19 (TC=19)**. Se dividen en 4 subtipos según los bits 6-8 del campo ME:

- **Subtipo 1 y 2:** Velocidad en tierra (*ground speed*).
- **Subtipo 3 y 4:** Velocidad verdadera o indicada en el aire (solo cuando no hay GNSS disponible).

---

### **Campos principales del mensaje**

| **Campo** | **Bits en ME** | **Descripción** |
|-----------|----------------|------------------------------------------------------------------------------|
| **Type Code (TC)** | 1-5 | Identifica el mensaje como velocidad en vuelo (valor 19 - binario `10011`). |
| **Subtipo (ST)** | 6-8 | Determina si el mensaje es de velocidad en tierra o aire. |
| **Intent Change Flag (IC)** | 9 | Indica si hay un cambio de intención de vuelo. |
| **IFR Capability Flag (IFR)** | 10 | Indica si la aeronave tiene capacidad IFR. |
| **Navigation Uncertainty Category (NUC)** | 11-13 | Indica precisión del GNSS (*NUCr* para ADS-B v0, *NUCv* para v1 y v2). |
| **Velocidad Vertical (VR)** | 38-46 | Se calcula como: \( VR = 64 \times (\text{valor decimal} - 1) \) en ft/min. |
| **Diferencia entre GNSS y altitud barométrica (dAlt)** | 50-56 | Se calcula como: \( dAlt = 25 \times (\text{valor decimal}) \) en ft. |

---

### **Decodificación de velocidad**

#### **Velocidad vertical:**
- El bit 36 (**VrSrc**) indica la fuente (0 = GNSS, 1 = Barométrica).
- El bit 37 (**Svr**) indica si la aeronave sube (0) o baja (1).
- Ejemplo:
  - Para el mensaje A: VR = -832 ft/min (descenso).
  - Para el mensaje B: VR = -2304 ft/min (descenso).

#### **Diferencia de altitud GNSS/Baro:**
- Bit 49 (**SDif**) indica el signo: 0 si GNSS está sobre Baro, 1 si está debajo.
- Valor en ft: \( dAlt = 25 \times \text{valor decimal} \).

---

### **Decodificación de velocidad en tierra y aire**

#### **Subtipo 1 y 2 (Ground Speed):**
- Velocidad Este-Oeste (**Vew**), dirección (**Dew**).
- Velocidad Norte-Sur (**Vns**), dirección (**Dns**).
- Cálculo:  
  - **Subtipo 1:** \( V = \text{valor decimal} - 1 \) (en nudos).
  - **Subtipo 2:** \( V = 4 \times (\text{valor decimal} - 1) \) (para aviones supersónicos, pero no se usa en la actualidad).

#### **Subtipo 3 y 4 (Airspeed):**
- Similar a *ground speed* pero usado cuando GNSS no está disponible.
- **Subtipo 3** es raro en la práctica.
- **Subtipo 4** es para aviones supersónicos.

---

### **Conclusión**
El mensaje de velocidad en vuelo (TC=19) proporciona velocidad horizontal y vertical, junto con información de incertidumbre y diferencias de altitud. Su decodificación es más sencilla que la de posición, ya que no usa codificaciones complejas.

