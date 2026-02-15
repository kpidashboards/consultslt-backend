const router = require('express').Router()
const Empresa = require('../models/Empresa')
const Obrigacao = require('../models/Obrigacao')
const Guia = require('../models/Guia')
const Alerta = require('../models/Alerta')

router.get('/', async (req, res) => {
  try {
    res.json({
      empresas: await Empresa.countDocuments(),
      obrigacoesPendentes: await Obrigacao.countDocuments({ status: 'pendente' }),
      guiasEmitidas: await Guia.countDocuments(),
      guiasPagas: await Guia.countDocuments({ status: 'paga' }),
      alertasNovos: await Alerta.countDocuments({ status: 'novo' })
    })
  } catch {
    res.json({
      empresas: 0,
      obrigacoesPendentes: 0,
      guiasEmitidas: 0,
      guiasPagas: 0,
      alertasNovos: 0
    })
  }
})

module.exports = router
