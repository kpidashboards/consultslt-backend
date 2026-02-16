const mongoose = require('mongoose')

const FiscalIrisSchema = new mongoose.Schema({
  cnpj: { type: String, required: true },
  empresa: { type: String, required: true },
  periodo: { type: String, required: true },
  receitaBruta12M: { type: Number, required: true },
  receitaMensal: { type: Number, required: true },
  folhaSalarios12M: { type: Number, required: true },
  fatorR: { type: Number, required: true },
  anexo: { type: String, required: true },
  valorDAS: { type: Number, required: true },
  certidoes: {
    status: { type: String, required: true },
    detalhes: { type: Array, default: [] },
  },
  pendencias: [
    {
      descricao: { type: String },
      valor: { type: Number },
    },
  ],
  historico: [
    {
      acao: { type: String },
      data: { type: Date },
      userId: { type: String },
    },
  ],
  userId: { type: String, required: true },
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now },
  deletedAt: { type: Date, default: null },
  ecacData: {
    certidoes: { type: Array, default: [] },
    pendencias: { type: Array, default: [] },
  },
})

module.exports = mongoose.model('FiscalIris', FiscalIrisSchema)