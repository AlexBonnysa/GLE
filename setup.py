from setuptools import setup

setup(name="Valis-App",  # Nombre
    version="0.5",  # Versión de desarrollo
    description="Aplicación de captura de datos en planta",  # Descripción del funcionamiento
    author="Javier García",  # Nombre del autor
    author_email='javier.garcia@lis-solutions,es',  # Email del autor
    license="GPL",  # Licencia: MIT, GPL, GPL 2.0...
    url="http://lis-solutions.es",  # Página oficial (si la hay)
    packages=['Application'],
    install_requires=[i.strip() for i in open("requeriments.txt").readlines()],
)