const express = require('express');
const router = express.Router();
const { ObjectId } = require('mongodb');
const db = require('../db'); // Supondo que exista um módulo para conexão com o MongoDB

// Mock para consultas ao e-CAC
router.get('/ecac/certidoes/:cnpj', async (req, res) => {
  const { cnpj } = req.params;
  console.log(`Consulta de certidões para o CNPJ: ${cnpj}`);

  const certidoes = {
    status: 'regular',
    consultadoEm: new Date().toISOString(),
  };

  // Registrar consulta no banco
  await db.collection('fiscal_iris').updateOne(
    { cnpj },
    { $set: { certidoes } },
    { upsert: true }
  );

  res.status(200).json(certidoes);
});

router.get('/ecac/pendencias/:cnpj', async (req, res) => {
  const { cnpj } = req.params;
  console.log(`Consulta de pendências para o CNPJ: ${cnpj}`);

  const pendencias = [
    { descricao: 'DAS em atraso', periodo: '01/2025' },
    { descricao: 'Multa por atraso', periodo: '12/2024' },
  ];

  // Registrar consulta no banco
  await db.collection('fiscal_iris').updateOne(
    { cnpj },
    { $set: { pendencias } },
    { upsert: true }
  );

  res.status(200).json(pendencias);
});

// CRUD do módulo fiscal (IRIS)
router.post('/iris', async (req, res) => {
  try {
    const data = req.body;
    data.createdAt = new Date();
    data.updatedAt = new Date();

    const result = await db.collection('fiscal_iris').insertOne(data);
    res.status(201).json(result.ops[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/iris', async (req, res) => {
  try {
    const calculos = await db.collection('fiscal_iris').find({ deletedAt: null }).toArray();
    res.status(200).json(calculos);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/iris/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const calculo = await db.collection('fiscal_iris').findOne({ _id: ObjectId(id), deletedAt: null });

    if (!calculo) {
      return res.status(404).json({ error: 'Cálculo não encontrado' });
    }

    res.status(200).json(calculo);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.put('/iris/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const data = req.body;
    data.updatedAt = new Date();

    const result = await db.collection('fiscal_iris').updateOne(
      { _id: ObjectId(id), deletedAt: null },
      { $set: data }
    );

    if (result.matchedCount === 0) {
      return res.status(404).json({ error: 'Cálculo não encontrado' });
    }

    res.status(200).json({ message: 'Cálculo atualizado com sucesso' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.delete('/iris/:id', async (req, res) => {
  try {
    const { id } = req.params;

    const result = await db.collection('fiscal_iris').updateOne(
      { _id: ObjectId(id), deletedAt: null },
      { $set: { deletedAt: new Date() } }
    );

    if (result.matchedCount === 0) {
      return res.status(404).json({ error: 'Cálculo não encontrado' });
    }

    res.status(200).json({ message: 'Cálculo excluído com sucesso' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;