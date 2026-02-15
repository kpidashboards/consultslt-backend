const router = require('express').Router()
const Empresa = require('../models/Empresa')

router.get('/', async (_, res) => {
  res.json(await Empresa.find())
})

router.post('/', async (req, res) => {
  const empresa = await Empresa.create(req.body)
  res.status(201).json(empresa)
})

router.put('/:id', async (req, res) => {
  await Empresa.findByIdAndUpdate(req.params.id, req.body)
  res.sendStatus(204)
})

router.delete('/:id', async (req, res) => {
  await Empresa.findByIdAndDelete(req.params.id)
  res.sendStatus(204)
})

module.exports = router
