"""
cortex.sovereign — Kernel Lingüístico Nativo
============================================
8 capas: planificador · programador · forja · verificador
         memoria · libro_mayor · renderizador · política

"Cuando el idioma del código coincide con el idioma del pensamiento,
 el código se convierte en documentación viva."

El software es una abstracción temporal; el pensamiento es la verdad.
"""

from .gobernador import GobernadorDimensional, GobernadorEstabilidad, EstadoPID
from .memoria import AlmacenMemoria
from .membrana import MembranaPersistencia, PropuestaHecho, ResultadoGuardia, ResultadoSellado
from .forja import Forja
from .planificador import Planificador
from .motor import MotorSoberano, EstadoEjecucion
from .ganchos import RegistroGanchos, EventoGancho, ResultadoGancho, AccionGancho
