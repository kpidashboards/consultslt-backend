const router = require('express').Router()
const multer = require('multer')
const tesseract = require('tesseract.js')
const Documento = require('../models/Documento')
const path = require('path')

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, 'backend/src/storage'),
  filename: (req, file, cb) => cb(null, Date.now() + '-' + file.originalname)
})
const upload = multer({ storage })

router.post('/upload', upload.single('file'), async (req, res) => {
  try {
    const filePath = path.resolve(req.file.path)
    const ocrResult = await tesseract.recognize(filePath, 'por')
    const doc = await Documento.create({
      empresaId: req.body.empresaId,
      nome: req.file.originalname,
      arquivo: req.file.filename,
      status: 'processado',
      resultadoOCR: ocrResult.data.text
    })
    res.status(201).json(doc)
  } catch (err) {
    res.status(500).json({ error: 'Falha no OCR', details: err.message })
  }
})

router.get('/', async (_, res) => {
  res.json(await Documento.find())
})

module.exports = router
