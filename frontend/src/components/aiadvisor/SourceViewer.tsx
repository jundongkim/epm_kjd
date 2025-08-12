import React from 'react'

type Props = {
  open: boolean
  onClose: () => void
  safeFilename: string
  page?: number
}

export default function SourceViewer({ open, onClose, safeFilename, page }: Props) {
  if (!open) return null
  const base = `/api/v1/aiadvisor/documents/view/by-safe/${encodeURIComponent(safeFilename)}`
  const src = page ? `${base}#page=${page}` : base

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
      <div className="bg-white w-[92vw] h-[86vh] rounded shadow-lg overflow-hidden">
        <div className="p-2 flex justify-between items-center border-b">
          <div className="text-sm font-medium">출처 보기</div>
          <button onClick={onClose} className="text-xs px-2 py-1 rounded bg-muted hover:bg-muted/80">닫기</button>
        </div>
        <iframe src={src} className="w-full h-full" />
      </div>
    </div>
  )
}


