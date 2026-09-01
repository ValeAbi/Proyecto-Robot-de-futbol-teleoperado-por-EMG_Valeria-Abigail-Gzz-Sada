# Teleoperación Gestual con EMG y Lógica Difusa

## 📘 Descripción
Este proyecto desarrolla un sistema de **teleoperación gestual** que traduce la actividad muscular del usuario en comandos direccionales para un robot móvil.  
Integra **percepción biológica**, **procesamiento inteligente** y **ejecución robótica**, con aplicaciones potenciales en rehabilitación, asistencia remota y control inclusivo de dispositivos.

---

## 🎯 Objetivo
Demostrar la viabilidad de un ciclo completo de interacción humano–máquina mediante:
- Captura de señales electromiográficas (EMG).
- Procesamiento con lógica difusa.
- Control inalámbrico de un robot móvil.

---

## 🛠️ Metodología
1. **Adquisición de señales EMG**  
   - Electrodos conectados a sensores **EMG8232**.  
   - Captura de actividad muscular real del usuario.

2. **Procesamiento con lógica difusa**  
   - Librería **scikit-fuzzy (skfuzzy)**.  
   - Funciones trapezoidales y triangulares para definir grados de pertenencia.  
   - Reglas difusas para determinar acciones: **adelante, atrás, paro**.

3. **Comunicación inalámbrica**  
   - Dos módulos **ESP32** conectados vía **WiFi WLAN**.  
   - Emisor: percepción y procesamiento de señales.  
   - Receptor: interpretación de comandos y control de motores con **DRV8833**.

---

## ⚙️ Tecnologías y Herramientas
- **ESP32** (emisor y receptor)  
- **Sensores EMG8232**  
- **DRV8833** (controlador de motores)  
- **Python / MicroPython**  
- **scikit-fuzzy (skfuzzy)**  
- **WiFi WLAN** para transmisión de datos  
- **Dashboard HTML** para visualización  

---

## 🚀 Resultados esperados
- Traducción eficiente de gestos musculares en comandos robóticos.  
- Optimización de transmisión de datos (solo cambios de estado).  
- Prototipo modular, probado por etapas antes de la integración final.  

---

## 📂 Estructura del repositorio
