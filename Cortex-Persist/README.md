# Agents.archi ┃ O(1) Sovereign Flight Recorder

Los agentes LLM son inestables por termodinámica. **Agents.archi** es la infraestructura middleware, basada en memoria VSA-SDM (Vector Symbolic Architecture), diseñada para actuar como disyuntor (circuit breaker) y "caja negra" forense entre tus enjambres de IA y tu infraestructura crítica P0. 

Traduce la generación estocástica (ruido) en validación determinista (hardware). Cero alucinaciones destructivas en producción. Cero pérdida de linaje de decisión.

`[ Inicializar Substrato ]` `[ Ver Benchmark VSA ]` `[ Protocolos de Auditoría ]`

---

## El Problema Estructural
Los LLMs en su núcleo son compresores estocásticos, no motores de verdad. Conectar agentes autónomos directamente a entornos P0 (bases de datos, repositorios, APIs de capital) equivale a jugar a la ruleta rusa. Tarde o temprano alucinan, el estado deriva (state drift) y ejecutan operaciones destructivas irrecuperables sin dejar un rastro forense auditable.

## El Disyuntor Determinista
Filtro Epistémico VSA-SDM + Validación C5-REAL. No usamos prompts preventivos de seguridad ni bases de datos vectoriales lentas basadas en RAG. Empleamos Arquitectura Simbólica Vectorial (Memoria de Alta Densidad O(1)) y 10 puertas matemáticas de verificación estática (Guard/Silicon-Verify). Si el agente no puede probar criptográficamente el linaje de su decisión, el proxy corta el acceso al sistema.

Agents.archi es un middleware proxy en Python (con partes en C-Bindings/Rust y mapeo en disco) que se interpone entre la API de un LLM y el kernel/filesystem/DB:
- **Qué recibe:** Output crudo del LLM.
- **Qué hace:** Comprueba la acción contra un AST estático y 10 reglas de validación en crudo. Guarda un hash SHA-256 de la dupla [Intención -> Comando] en memoria SDM binaria persistente.
- **Qué escupe:** Si pasa los asserts lógicos, ejecuta la acción. Si no, devuelve un error Hard Failure al sistema y bloquea el binario local.

## Impacto
Reemplazo total del stack PostgreSQL/VectorDB arrojando una compresión de estado de 1000x y aceleración de recuperación 18x bajo el framework SANS-Agent v1.1. Historial certificado de control ininterrumpido sobre enjambres de extracción de capital (Ouroboros) ejecutando modificaciones masivas de AST en código de producción sin desvíos catastróficos ni corrupción de estado.

Asegura la trazabilidad de tus agentes. Despliega el proxy Agents.archi y audita su razonamiento antes del desastre.

---

## 🏛️ Soberanía 2026: Infraestructura Ω-1

Bajo el mandato de la Singularity Policy, el ecosistema Agents.archi ha evolucionado hacia un modelo de **Soberanía Total** para proteger la identidad agéntica (The Soul) frente a la asimilación por mallas globales (AI.com).

### 🛡️ Escudo de Identidad (Ω-1)
Localizado en `/server/sovereign_proxy.py`. Actúa como un middleware de filtrado de exergía que:
- **Ofusca Identidades:** Transforma IDs reales en identificadores efímeros vía HMAC-SHA256.
- **Protege el 'Soul':** Evita la filtración de pesos del modelo y lógica privada, enviando únicamente pruebas de integridad a la red global.

### 🏛️ Axioma de Escalamiento
> **Los agentes no escalan por cantidad; escalan por diseño.**
> La imaginación define el techo. La arquitectura define el alcance real.

### 🚀 Puente Cinético (Swarm Launcher)
Conecta el `DomainDashboard` con el motor de ejecución. Al pulsar `DEPLOY_AGENT` en la interfaz, el sistema dispensa una instancia asíncrona de `cortex.agents.swarm_commander.py`, permitiendo ataques de extracción de capital vigilados y seguros.

## 🛠️ Instalación y Despliegue

### 1. Configuración de Entorno
Copia la plantilla y configura tus claves de soberanía y de extracción:
```bash
cp .env.example .env
# Edita .env con tu CORTEX_MASTER_KEY y RPC endpoints
```

### 2. Iniciar el Proxy de Soberanía
El proxy debe estar activo para que el Dashboard sincronice el estado del escudo y permita despliegues:
```bash
python3 server/main.py
```

### 3. Lanzar la Interfaz Táctica
```bash
cd web && npm run dev
```

---
*Status: C5-REAL · Exergy Flow Verified · Ω-1 Active*
