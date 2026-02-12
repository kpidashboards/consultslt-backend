Autenticação


POST
/api/auth/login
Login

Usuários


GET
/api/usuarios/usuarios/
Listar Usuarios



POST
/api/usuarios/usuarios/
Criar Usuario



GET
/api/usuarios/usuarios/{usuario_id}
Obter Usuario



PUT
/api/usuarios/usuarios/{usuario_id}
Atualizar Usuario



DELETE
/api/usuarios/usuarios/{usuario_id}
Excluir Usuario


Empresas


GET
/api/empresas/empresas/
Listar Empresas


POST
/api/empresas/empresas/
Criar Empresa


PUT
/api/empresas/empresas/{empresa_id}
Atualizar Empresa


DELETE
/api/empresas/empresas/{empresa_id}
Deletar Empresa

Fiscal


POST
/api/fiscal/fiscal/
Criar Fiscal


GET
/api/fiscal/fiscal/
Listar Fiscal


GET
/api/fiscal/fiscal/{fiscal_id}
Obter Fiscal


PUT
/api/fiscal/fiscal/{fiscal_id}
Atualizar Fiscal

Documentos


GET
/api/documentos/documentos/
Listar Documentos


POST
/api/documentos/documentos/
Criar Documento


GET
/api/documentos/documentos/{documento_id}
Obter Documento

Obrigações


GET
/api/obrigacoes/obrigacoes/
Lista todas as obrigações fiscais

Robôs


GET
/api/robots/
Listar Robots


POST
/api/robots/
Criar Robot

Auditoria


GET
/api/auditoria/auditoria/
Listar Auditorias


POST
/api/auditoria/auditoria/
Criar Auditoria


GET
/api/auditoria/auditoria/{id}
Obter Auditoria

Certidões


POST
/api/certidoes/certidoes/
Criar Certidao


GET
/api/certidoes/certidoes/
Listar Certidoes


GET
/api/certidoes/certidoes/{certidao_id}
Obter Certidao


PUT
/api/certidoes/certidoes/{certidao_id}
Atualizar Certidao


DELETE
/api/certidoes/certidoes/{certidao_id}
Deletar Certidao


POST
/api/certidoes/certidoes/atualizar-status
Atualizar Status Certidoes

Configurações


POST
/api/configuracoes/configuracoes/
Criar Configuracao


GET
/api/configuracoes/configuracoes/
Listar Configuracoes


GET
/api/configuracoes/configuracoes/chave/{chave}
Obter Configuracao Por Chave


GET
/api/configuracoes/configuracoes/{config_id}
Obter Configuracao Por Id


PUT
/api/configuracoes/configuracoes/{config_id}
Atualizar Configuracao


DELETE
/api/configuracoes/configuracoes/{config_id}
Deletar Configuracao

Débitos


POST
/api/debitos/debitos/
Criar Debito


GET
/api/debitos/debitos/
Listar Debitos


GET
/api/debitos/debitos/{debito_id}
Obter Debito


PUT
/api/debitos/debitos/{debito_id}
Atualizar Debito


DELETE
/api/debitos/debitos/{debito_id}
Deletar Debito


GET
/api/debitos/debitos/resumo/geral
Resumo Debitos

Guias


POST
/api/guias/guias/
Criar Guia


GET
/api/guias/guias/
Listar Guias


GET
/api/guias/guias/{guia_id}
Obter Guia


PUT
/api/guias/guias/{guia_id}
Atualizar Guia


DELETE
/api/guias/guias/{guia_id}
Deletar Guia


GET
/api/guias/guias/proximos-vencimentos/lista
Proximos Vencimentos

OCR e Automação Documental


POST
/api/ocr/ocr/processar
Processar Documento Ocr


POST
/api/ocr/ocr/processar-lote
Processar Lote Ocr


GET
/api/ocr/ocr/documentos
Listar Documentos Ocr


GET
/api/ocr/ocr/estatisticas
Obter Estatisticas Ocr


GET
/api/ocr/ocr/documentos/{documento_id}
Obter Documento Ocr


GET
/api/ocr/ocr/tipos-suportados
Listar Tipos Suportados

Relatórios


POST
/api/relatorios/relatorios/
Criar Relatorio


GET
/api/relatorios/relatorios/
Listar Relatorios


GET
/api/relatorios/relatorios/{relatorio_id}
Obter Relatorio


DELETE
/api/relatorios/relatorios/{relatorio_id}
Deletar Relatorio


GET
/api/relatorios/relatorios/dashboard/resumo
Resumo Dashboard

SharePoint


GET
/api/sharepoint/sharepoint/status
Get Sharepoint Status


POST
/api/sharepoint/sharepoint/list-files
List Sharepoint Files


GET
/api/sharepoint/sharepoint/folders
List Root Folders


GET
/api/sharepoint/sharepoint/robots/ingestion/status
Get Ingestion Robot Status


POST
/api/sharepoint/sharepoint/robots/ingestion/run
Run Ingestion Once

Health


GET
/api/health/health
Health Check


GET
/api/health/health/detailed
Health Detailed

default


GET
/
Root