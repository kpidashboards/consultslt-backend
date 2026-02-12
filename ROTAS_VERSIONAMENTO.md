# Tabela Final de Rotas, Versionamento e Persistência

| Rota/Service | Método | Repository | Versionamento | Persistência | Observações |
|--------------|--------|------------|--------------|-------------|-------------|
| /usuarios (GET, POST, PUT, DELETE) | API | UsersRepository | Sim | MongoDB | 100% versionado, histórico preservado |
| /relatorios (GET, POST, DELETE) | API | RelatoriosRepository | Sim | MongoDB | 100% versionado, histórico preservado |
| /relatorios/dashboard/resumo | API | DocumentosRepository, ObrigacoesRepository, GuiasRepository, EmpresasRepository | N/A | MongoDB | Apenas leitura, contagem e agregação |
| /alertas (GET, POST, PATCH, DELETE) | API | AlertasRepository | Sim | MongoDB | 100% versionado, histórico preservado |
| /obrigacoes (services) | Service | ObrigacoesRepository | Sim | MongoDB | 100% versionado, histórico preservado |
| /ocr_documentos (services) | Service | OcrDocumentosRepository | Sim | MongoDB | 100% versionado, histórico preservado |
| /documentos (services) | Service | DocumentosRepository | Sim | MongoDB | 100% versionado, histórico preservado |
| /guias (services) | Service | GuiasRepository | Sim | MongoDB | 100% versionado, histórico preservado |
| /debitos (services) | Service | DebitosRepository | Sim | MongoDB | 100% versionado, histórico preservado |
| /certidoes (services) | Service | CertidoesRepository | Sim | MongoDB | 100% versionado, histórico preservado |
| /configuracoes (services) | Service | ConfiguracoesRepository | Sim | MongoDB | 100% versionado, histórico preservado |
| /auditoria (services) | Service | AuditoriaRepository | Sim | MongoDB | 100% versionado, histórico preservado |

## Legenda
- **Versionamento:** Sim = version, valid_from, valid_to, previous_version_id implementados
- **Persistência:** MongoDB, sem mock, sem dados temporários
- **Observações:** Histórico nunca é sobrescrito ou deletado

---

**Confirmação explícita:**

- ❌ Ainda existe acesso direto ao banco nesses arquivos? **NÃO**
- ✔️ Todas as rotas/services agora usam repository? **SIM**
- ✔️ Escritas estão versionadas? **SIM, 100%**
