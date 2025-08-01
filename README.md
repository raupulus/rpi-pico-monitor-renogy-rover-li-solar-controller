# rpi-pico-monitor-renogy-rover-li-solar-controller

Este proyecto permite obtener la información de un controlador solar `Renogy 
Rover LI` desde una raspberry pi pico para subirlo a mi propia api y/o a un 
home assistant de forma opcional.


---

PROYECTO EN DESARROLLO

--- 

Sitio web del autor: [https://raupulus.dev](https://raupulus.dev)

![Imagen del Proyecto](docs/images/img1.jpg "Imagen Principal de raspberry pi pico w")

Repository [https://gitlab.com/raupulus/rpi-pico-template-project-micropython](https://gitlab.com/raupulus/rpi-pico-template-project-micropython)

Una de las ventajas es que en **Models** ya disponemos de dos modelos que
suelen ser fundamentales para mi: 

- API: Para interactuar fácilmente con mis apis enviando/recibiendo datos
- RpiPico: Representa a la raspberry: incluye conectividad wireless, gestión de
  ADC integrado, puede obtener información de la red y conectar a redes 
  alternativas por si nos desplazamos (usamos en varias ubicaciones) o 
  necesitamos un respaldo, información de temperatura...

Además de algunos parámetros básicos en el archivo de variables de entorno
que usamos como base **.env.example.py**

<p align="center">
  <img src="docs/images/2.jpg" alt="Raspberry pi pico w image 1" height="150">
  <img src="docs/images/3.jpg" alt="Raspberry pi pico w image 2" height="150">
  <img src="docs/images/4.jpg" alt="Raspberry pi pico w image 3" height="150">
  <img src="docs/images/scheme_thumbnail.jpg" alt="Raspberry pi pico w esquema de pines" height="150">
</p>

## Software y Firmware

- IDE/Editor (EJ: thonny, pycharm o vscode)
- [MicroPython 1.23](https://micropython.org/download/rp2-pico/) instalado 
  en la Raspberry Pi Pico.

## Contenido del Repositorio

- **src/**: Código fuente del proyecto.
- **src/Models**: Modelos/Clases para separar entidades que intervienen.
- **docs/**: Documentación adicional, esquemas y guías de instalación.

## Instalación

1. **Instalación de MicroPython:**
   - Asegúrate de que MicroPython esté instalado en tu Raspberry Pi Pico. Puedes seguir las instrucciones en la [documentación oficial](https://docs.micropython.org/en/latest/rp2/quickref.html).

2. **Cargar el Código:**
   - Descarga o clona este repositorio.
   - Copia el archivo *.env.example.py* a *env.py* y rellena los datos para 
     conectar al wireless además de la ruta para subir datos a tu API.
   - Copia los archivos en la carpeta `src/` a la Raspberry Pi Pico.

## Esquema de la raspberry pi pico

![Imagen del Proyecto](docs/images/scheme.png "Esquema de pines para la raspberry pi pico")

## Licencia

Este proyecto está licenciado bajo la Licencia GPLv3. Consulta el archivo 
LICENSE para más detalles.


## TODO

- Api_OLD.py es el modelo que usaba en la raspberry pi 2, ahora hay que 
  utilizar Api.py e implementar la subida ahí.
- Implementar subida al home assistant, añadir su variable al .env.example y 
  controlar que puede estar apagado, si falla pues se ignora hasta la 
  próxima lectura.
- Se debe leer, subir a la api, subir al home assistant (si estuviera 
  configurado) y dormir durante 1 minuto.
- En el modelo de la raspberry, devolver de un método datos de estado: carga 
  de batería restante estimada, temperatura interna, wifi conectado, wifi 
  fuerza señal.
- Al iniciar la raspberry y estar conectada a internet, debe sincronizarse 
  en hora con server ntp
- A la api hay que enviar datos dentro de "microcontroller" como 
  añadido a los datos de cada petición, es decir, del diccionario que se 
  envía hay que añadir microcontroller con los datos que devuelve el método 
  de la raspberry para: carga 
  de batería restante estimada, temperatura interna, wifi conectado, wifi 
  fuerza señal.
- Mirar las formas de dormir el microcontrolador para las esperas de 1m, quizás
  no interese que se duerma completamente para ahorrar conectar luego a 
  wireless.
- Crear documentación indicando datos enviados a cada api