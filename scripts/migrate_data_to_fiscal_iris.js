const mongoose = require('mongoose');
const FiscalIris = require('../src/models/FiscalIris');
const OldCollection1 = require('../src/models/OldCollection1'); // Exemplo de coleção antiga
const OldCollection2 = require('../src/models/OldCollection2'); // Exemplo de coleção antiga

mongoose.connect('mongodb://localhost:27017/consultslt_db', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

const migrateData = async () => {
  try {
    console.log('Iniciando migração de dados...');

    // Exemplo de migração de dados da coleção antiga para a nova estrutura
    const oldData1 = await OldCollection1.find();
    const oldData2 = await OldCollection2.find();

    for (const data of oldData1) {
      await FiscalIris.create({
        cnpj: data.cnpj,
        empresa: data.empresa,
        periodo: data.periodo,
        receitaBruta12M: data.receitaBruta12M,
        receitaMensal: data.receitaMensal,
        folhaSalarios12M: data.folhaSalarios12M,
        fatorR: data.fatorR,
        anexo: data.anexo,
        valorDAS: data.valorDAS,
        certidoes: data.certidoes,
        pendencias: data.pendencias,
        historico: data.historico,
        userId: data.userId,
        createdAt: data.createdAt,
        updatedAt: data.updatedAt,
        deletedAt: data.deletedAt,
        ecacData: {
          certidoes: [],
          pendencias: [],
        },
      });
    }

    for (const data of oldData2) {
      await FiscalIris.updateOne(
        { cnpj: data.cnpj, periodo: data.periodo },
        {
          $set: {
            ecacData: {
              certidoes: data.certidoes,
              pendencias: data.pendencias,
            },
          },
        }
      );
    }

    console.log('Migração concluída com sucesso!');
    process.exit(0);
  } catch (error) {
    console.error('Erro durante a migração:', error);
    process.exit(1);
  }
};

migrateData();