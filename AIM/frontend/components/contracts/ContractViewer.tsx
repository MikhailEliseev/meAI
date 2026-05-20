"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"

interface Contract {
  id: string
  contractNumber: string
  contractType: "service_agreement" | "nda" | "addendum"
  clientName: string
  status: "draft" | "sent" | "signed" | "declined" | "expired"
  createdAt: string
  signedAt?: string
  amount?: number
  documentId?: string
}

interface ContractViewerProps {
  clientId?: string
  className?: string
}

export default function ContractViewer({
  clientId,
  className = "",
}: ContractViewerProps) {
  const [contracts, setContracts] = useState<Contract[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedContract, setSelectedContract] = useState<Contract | null>(null)
  const [filter, setFilter] = useState<string>("all")

  useEffect(() => {
    fetchContracts()
  }, [clientId, filter])

  const fetchContracts = async () => {
    try {
      setLoading(true)

      // STUB: Mock data for development
      // TODO: Replace with real API call in Phase 12
      await new Promise(resolve => setTimeout(resolve, 500))

      const mockContracts: Contract[] = [
        {
          id: "1",
          contractNumber: "AIM-2026-001",
          contractType: "service_agreement",
          clientName: "Стоматология Дента Плюс",
          status: "signed",
          createdAt: "2026-05-01T10:00:00Z",
          signedAt: "2026-05-02T14:30:00Z",
          amount: 250000,
          documentId: "STUB-DOC-001",
        },
        {
          id: "2",
          contractNumber: "NDA-2026-001",
          contractType: "nda",
          clientName: "Стоматология Дента Плюс",
          status: "signed",
          createdAt: "2026-05-01T09:00:00Z",
          signedAt: "2026-05-01T15:00:00Z",
          documentId: "STUB-DOC-002",
        },
        {
          id: "3",
          contractNumber: "AIM-2026-002",
          contractType: "service_agreement",
          clientName: "Клиника Здоровье",
          status: "sent",
          createdAt: "2026-05-10T11:00:00Z",
          amount: 150000,
          documentId: "STUB-DOC-003",
        },
        {
          id: "4",
          contractNumber: "AIM-2026-003",
          contractType: "service_agreement",
          clientName: "Медицинский Центр",
          status: "draft",
          createdAt: "2026-05-15T16:00:00Z",
          amount: 300000,
        },
      ]

      // Filter contracts
      let filtered = mockContracts
      if (filter !== "all") {
        filtered = mockContracts.filter(c => c.status === filter)
      }
      if (clientId) {
        filtered = filtered.filter(c => c.id === clientId)
      }

      setContracts(filtered)
    } catch (error) {
      console.error("Failed to fetch contracts:", error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: Contract["status"]) => {
    const badges = {
      draft: { label: "Черновик", color: "bg-surface-3 text-text-muted" },
      sent: { label: "Отправлен", color: "bg-accent/15 text-accent" },
      signed: { label: "Подписан", color: "bg-semantic-success/15 text-semantic-success" },
      declined: { label: "Отклонён", color: "bg-semantic-error/15 text-semantic-error" },
      expired: { label: "Истёк", color: "bg-amber-400/15 text-amber-400" },
    }

    const badge = badges[status]
    return (
      <span className={`px-3 py-1 rounded-md text-sm font-medium ${badge.color}`}>
        {badge.label}
      </span>
    )
  }

  const getContractTypeName = (type: Contract["contractType"]) => {
    const types = {
      service_agreement: "Договор на оказание услуг",
      nda: "Соглашение о конфиденциальности",
      addendum: "Дополнительное соглашение",
    }
    return types[type]
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
      year: "numeric",
    })
  }

  const formatAmount = (amount?: number) => {
    if (!amount) return "—"
    return new Intl.NumberFormat("ru-RU", {
      style: "currency",
      currency: "RUB",
      minimumFractionDigits: 0,
    }).format(amount)
  }

  const handleDownload = async (contract: Contract) => {
    // STUB: Mock download
    console.log("Downloading contract:", contract.contractNumber)
    alert(`STUB: Скачивание договора ${contract.contractNumber}`)
  }

  const handleResend = async (contract: Contract) => {
    if (!contract.documentId) return

    try {
      // STUB: Mock resend
      await new Promise(resolve => setTimeout(resolve, 500))
      alert(`Уведомление отправлено повторно для договора ${contract.contractNumber}`)
    } catch (error) {
      console.error("Failed to resend:", error)
      alert("Ошибка при отправке уведомления")
    }
  }

  const handleCancel = async (contract: Contract) => {
    if (!contract.documentId) return

    const reason = prompt("Укажите причину отмены:")
    if (!reason) return

    try {
      // STUB: Mock cancel
      await new Promise(resolve => setTimeout(resolve, 500))
      alert(`Запрос на подпись отменён для договора ${contract.contractNumber}`)
      fetchContracts()
    } catch (error) {
      console.error("Failed to cancel:", error)
      alert("Ошибка при отмене запроса")
    }
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-12 ${className}`}>
        <div className="animate-spin rounded-md h-12 w-12 border-b-2 border-accent"></div>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-ink">Договоры</h2>

        {/* Filter */}
        <div className="flex gap-2">
          {["all", "draft", "sent", "signed"].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === status
                  ? "bg-accent text-white"
                  : "bg-surface-3 text-text-muted hover:bg-surface-2"
              }`}
            >
              {status === "all" ? "Все" : getStatusBadge(status as Contract["status"]).props.children}
            </button>
          ))}
        </div>
      </div>

      {/* Contracts List */}
      {contracts.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-text-subtle">Договоры не найдены</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {contracts.map((contract, index) => (
            <motion.div
              key={contract.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-surface-2 rounded-lg border border-border-hairline p-6 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Contract Number & Type */}
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-ink">
                      {contract.contractNumber}
                    </h3>
                    {getStatusBadge(contract.status)}
                  </div>

                  {/* Contract Type */}
                  <p className="text-sm text-text-muted mb-1">
                    {getContractTypeName(contract.contractType)}
                  </p>

                  {/* Client Name */}
                  <p className="text-sm text-text-muted mb-3">
                    Клиент: <span className="font-medium">{contract.clientName}</span>
                  </p>

                  {/* Details */}
                  <div className="flex items-center gap-6 text-sm text-text-subtle">
                    <div>
                      <span className="font-medium">Создан:</span> {formatDate(contract.createdAt)}
                    </div>
                    {contract.signedAt && (
                      <div>
                        <span className="font-medium">Подписан:</span> {formatDate(contract.signedAt)}
                      </div>
                    )}
                    {contract.amount && (
                      <div>
                        <span className="font-medium">Сумма:</span> {formatAmount(contract.amount)}/мес
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDownload(contract)}
                    className="px-4 py-2 bg-accent text-white rounded-lg hover:brightness-110 transition-colors text-sm font-medium"
                  >
                    Скачать PDF
                  </button>

                  {contract.status === "sent" && contract.documentId && (
                    <>
                      <button
                        onClick={() => handleResend(contract)}
                        className="px-4 py-2 bg-surface-3 text-text-muted rounded-lg hover:bg-surface-2 transition-colors text-sm font-medium"
                      >
                        Отправить повторно
                      </button>
                      <button
                        onClick={() => handleCancel(contract)}
                        className="px-4 py-2 bg-semantic-error/15 text-semantic-error rounded-md hover:bg-semantic-error/25 transition-colors text-sm font-medium"
                      >
                        Отменить
                      </button>
                    </>
                  )}

                  {contract.status === "draft" && (
                    <button
                      onClick={() => alert("STUB: Отправка на подпись")}
                      className="px-4 py-2 bg-semantic-success text-white rounded-lg hover:brightness-110 transition-colors text-sm font-medium"
                    >
                      Отправить на подпись
                    </button>
                  )}
                </div>
              </div>

              {/* STUB Notice */}
              {contract.documentId && (
                <div className="mt-4 p-3 bg-surface-3 border border-amber-400/30 rounded-md">
                  <p className="text-sm text-amber-400">
                    <span className="font-semibold">STUB:</span> Интеграция с Контур.Диадок будет реализована в Phase 12.
                    Document ID: {contract.documentId}
                  </p>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
