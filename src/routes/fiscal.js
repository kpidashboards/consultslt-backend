const router = require('express').Router()
const FiscalIris = require('../models/FiscalIris')

// POST: Criar novo cálculo fiscal com integração de dados do e-CAC
router.post('/', async (req, res) => {
  try {
    const { cnpj, empresa, periodo, receitaBruta12M, receitaMensal, folhaSalarios12M, userId } = req.body;

    // Simulação de cálculo de Fator R e DAS
    const fatorR = folhaSalarios12M / receitaBruta12M;
    const anexo = fatorR >= 0.28 ? 'Anexo III' : 'Anexo V';
    const valorDAS = receitaMensal * 0.18; // Exemplo de cálculo

    // Simulação de consulta ao e-CAC
    const ecacData = {
      certidoes: [{ status: 'regular', detalhes: [] }],
      pendencias: [{ descricao: 'Débito em aberto', valor: 1200.00 }]
    };

    const fiscal = await FiscalIris.create({
      cnpj,
      empresa,
      periodo,
      receitaBruta12M,
      receitaMensal,
      folhaSalarios12M,
      fatorR,
      anexo,
      valorDAS,
      certidoes: ecacData.certidoes[0],
      pendencias: ecacData.pendencias,
      userId,
      ecacData
    });

    res.status(201).json(fiscal);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
})

// GET: Listar cálculos fiscais com filtros
router.get('/', async (req, res) => {
  try {
    const { cnpj, periodo, status } = req.query;
    const query = { deletedAt: null };

    if (cnpj) query.cnpj = cnpj;
    if (periodo) query.periodo = periodo;
    if (status) query['certidoes.status'] = status;

    const fiscais = await FiscalIris.find(query);
    res.json(fiscais);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
})

// GET: Detalhar cálculo fiscal por ID
router.get('/:id', async (req, res) => {
  try {
    const fiscal = await FiscalIris.findById(req.params.id);
    if (!fiscal || fiscal.deletedAt) {
      return res.status(404).json({ error: 'Registro não encontrado' });
    }
    res.json(fiscal);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
})

// PUT: Atualizar cálculo fiscal e recalcular
router.put('/:id', async (req, res) => {
  try {
    const { receitaBruta12M, receitaMensal, folhaSalarios12M } = req.body;

    const fiscal = await FiscalIris.findById(req.params.id);
    if (!fiscal || fiscal.deletedAt) {
      return res.status(404).json({ error: 'Registro não encontrado' });
    }

    // Recalcular Fator R e DAS
    const fatorR = folhaSalarios12M / receitaBruta12M;
    const anexo = fatorR >= 0.28 ? 'Anexo III' : 'Anexo V';
    const valorDAS = receitaMensal * 0.18; // Exemplo de cálculo

    fiscal.set({
      ...req.body,
      fatorR,
      anexo,
      valorDAS,
      updatedAt: new Date(),
    });

    await fiscal.save();

    res.json(fiscal);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
})

// DELETE: Exclusão lógica
router.delete('/:id', async (req, res) => {
  try {
    const fiscal = await FiscalIris.findByIdAndUpdate(
      req.params.id,
      { deletedAt: new Date() },
      { new: true }
    );
    if (!fiscal) {
      return res.status(404).json({ error: 'Registro não encontrado' });
    }
    res.json({ message: 'Registro excluído logicamente' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
})

module.exports = router