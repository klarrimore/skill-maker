---
name: architecture-blueprint-generator
description: 'Comprehensive project architecture blueprint generator that analyzes codebases to create detailed architectural documentation. Automatically detects technology stacks and architectural patterns, generates visual diagrams, documents implementation patterns, and provides extensible blueprints for maintaining architectural consistency and guiding new development. Use when the user asks to document the architecture, produce an architecture blueprint or overview, map the system design, or create a reference for keeping new development architecturally consistent.'
---

# Project Architecture Blueprint Generator

Analyze a codebase and produce a single document, `Project_Architecture_Blueprint.md`, that captures the project's real architecture — patterns, boundaries, components, and cross-cutting concerns — so it can serve as a definitive reference for maintaining architectural consistency and guiding new development.

Base every statement on the **actual implementation**, not on textbook descriptions of the patterns you recognize. When the code and a "standard" pattern disagree, document what the code does.

## Parameters

Infer sensible defaults by inspecting the repository; ask the user only when a choice materially changes the output. Each parameter below lists its options and default.

- **Project type** — the primary technology stack. Default: auto-detect. (`.NET`, `Java`, `React`, `Angular`, `Python`, `Node.js`, `Flutter`, `Other`, or auto-detect.)
- **Architecture pattern** — the primary architectural style. Default: auto-detect. (`Clean Architecture`, `Microservices`, `Layered`, `MVVM`, `MVC`, `Hexagonal`, `Event-Driven`, `Serverless`, `Monolithic`, `Other`, or auto-detect.)
- **Diagram type** — Default: `C4`. (`C4`, `UML`, `Flow`, `Component`, or `None` for text-only descriptions.)
- **Detail level** — Default: `Comprehensive`. (`High-level`, `Detailed`, `Comprehensive`, `Implementation-Ready`.)
- **Include code examples** — Default: yes.
- **Include implementation patterns** — Default: yes.
- **Include architectural decision records** — Default: yes.
- **Emphasize extensibility** — Default: yes.

## Procedure

Work through the following sections in order. Sections marked *(optional)* are included only when the corresponding parameter is enabled; otherwise replace them with a one-line note (e.g. "Detailed implementation patterns vary across the codebase").

### 1. Architecture detection and analysis

- If project type is auto-detect, identify all technology stacks and frameworks in use by examining project and configuration files, package dependencies and import statements, framework-specific patterns and conventions, and build/deployment configurations. Otherwise focus on the specified stack's patterns and practices.
- If the architecture pattern is auto-detect, determine the pattern(s) by analyzing folder organization and namespacing, dependency flow and component boundaries, interface segregation and abstraction patterns, and communication mechanisms between components. Otherwise document how the specified pattern is implemented.

### 2. Architectural overview

- Provide a clear, concise explanation of the overall architectural approach.
- Document the guiding principles evident in the architectural choices.
- Identify architectural boundaries and how they are enforced.
- Note any hybrid patterns or adaptations of standard patterns.

### 3. Architecture visualization

If a diagram type is selected, create diagrams of that type at multiple levels of abstraction:

- A high-level architectural overview showing major subsystems.
- Component interaction diagrams showing relationships and dependencies.
- Data flow diagrams showing how information moves through the system.
- Ensure diagrams reflect the actual implementation, not theoretical patterns.

If diagram type is `None`, describe component relationships textually based on actual code dependencies: subsystem organization and boundaries, dependency directions and component interactions, and data flow and process sequences.

### 4. Core architectural components

For each architectural component discovered in the codebase, document:

- **Purpose and responsibility** — primary function within the architecture, business domains or technical concerns addressed, and boundaries/scope limitations.
- **Internal structure** — organization of classes/modules, key abstractions and their implementations, and design patterns used.
- **Interaction patterns** — how it communicates with others, interfaces exposed and consumed, dependency injection patterns, and event publish/subscribe mechanisms.
- **Evolution patterns** — how it can be extended, variation points and plugin mechanisms, and configuration/customization approaches.

### 5. Architectural layers and dependencies

- Map the layer structure as implemented.
- Document the dependency rules between layers.
- Identify abstraction mechanisms that enable layer separation.
- Note any circular dependencies or layer violations.
- Document dependency injection patterns used to maintain separation.

### 6. Data architecture

- Document domain model structure and organization.
- Map entity relationships and aggregation patterns.
- Identify data access patterns (repositories, data mappers, etc.).
- Document data transformation and mapping approaches.
- Note caching strategies and implementations.
- Document data validation patterns.

### 7. Cross-cutting concerns

Document the implementation patterns for each:

- **Authentication & authorization** — security model, permission enforcement, identity management, and security boundary patterns.
- **Error handling & resilience** — exception handling, retry and circuit-breaker implementations, fallback/graceful-degradation strategies, and error reporting/monitoring.
- **Logging & monitoring** — instrumentation patterns, observability implementation, diagnostic information flow, and performance monitoring.
- **Validation** — input validation strategies, business-rule validation, responsibility distribution, and error reporting.
- **Configuration management** — configuration sources, environment-specific strategies, secret management, and feature flags.

### 8. Service communication patterns

- Document service boundary definitions.
- Identify communication protocols and formats.
- Map synchronous vs. asynchronous communication.
- Document API versioning strategies.
- Identify service discovery mechanisms.
- Note resilience patterns in service communication.

### 9. Technology-specific patterns

For each detected (or specified) stack, document its architectural patterns. Apply the relevant checklist below:

- **.NET** — host and application model, middleware pipeline organization, framework service integration, ORM and data access, API implementation (controllers, minimal APIs), and DI container configuration.
- **Java** — application container and bootstrap, DI framework usage (Spring, CDI), AOP patterns, transaction boundary management, ORM configuration, and service implementation patterns.
- **React** — component composition and reuse, state management architecture, side-effect handling, routing/navigation, data fetching and caching, and rendering optimization.
- **Angular** — module organization, component hierarchy design, services and DI, state management, reactive programming patterns, and route guards.
- **Python** — module organization, dependency management, OOP vs. functional patterns, framework integration, and asynchronous programming.

### 10. Implementation patterns *(optional)*

Document concrete implementation patterns for key components:

- **Interface design** — segregation approaches, abstraction-level decisions, generic vs. specific interfaces, and default implementations.
- **Service implementation** — lifetime management, composition patterns, operation templates, and in-service error handling.
- **Repository implementation** — query patterns, transaction management, concurrency handling, and bulk operations.
- **Controller/API implementation** — request handling, response formatting, parameter validation, and versioning.
- **Domain model implementation** — entity patterns, value objects, domain events, and business-rule enforcement.

### 11. Testing architecture

- Document testing strategies aligned with the architecture.
- Identify test boundary patterns (unit, integration, system).
- Map test doubles and mocking approaches.
- Document test data strategies.
- Note testing tools and framework integration.

### 12. Deployment architecture

- Document deployment topology derived from configuration.
- Identify environment-specific architectural adaptations.
- Map runtime dependency resolution patterns.
- Document configuration management across environments.
- Identify containerization and orchestration approaches.
- Note cloud service integration patterns.

### 13. Extension and evolution patterns *(optional)*

Provide detailed guidance for extending the architecture:

- **Feature addition** — how to add features while preserving architectural integrity, where to place new components by type, dependency-introduction guidelines, and configuration-extension patterns.
- **Modification** — how to safely modify existing components, backward-compatibility strategies, deprecation patterns, and migration approaches.
- **Integration** — how to integrate new external systems, adapter patterns, anti-corruption layers, and service facades.

### 14. Architectural pattern examples *(optional)*

Extract representative code examples that illustrate key patterns: layer separation (interface/implementation separation, cross-layer communication, DI), component communication (service invocation, event publication/handling, message passing), and extension points (plugin registration and discovery, extension interface implementations, configuration-driven extension). Include enough context to show each pattern clearly, but keep examples concise and focused on the architectural concept.

### 15. Architectural decision records *(optional)*

Document key decisions evident in the codebase — architectural style choices, technology selections, and implementation-approach choices. For each decision, note the context that made it necessary, the factors considered, the resulting consequences (positive and negative), and the future flexibility or limitations it introduced.

### 16. Architecture governance

- Document how architectural consistency is maintained.
- Identify automated checks for architectural compliance.
- Note review processes evident in the codebase.
- Document architectural documentation practices.

### 17. Blueprint for new development

Create a clear guide for implementing new features:

- **Development workflow** — starting points for different feature types, component creation sequence, integration steps with the existing architecture, and testing approach by layer.
- **Implementation templates** — base class/interface templates for key components, standard file organization, dependency declaration patterns, and documentation requirements.
- **Common pitfalls** — architecture violations to avoid, common mistakes, performance considerations, and testing blind spots.

## Finishing

Record when the blueprint was generated and add recommendations for keeping it updated as the architecture evolves.
