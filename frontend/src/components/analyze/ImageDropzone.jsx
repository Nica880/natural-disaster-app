import { useCallback, useRef, useState } from 'react'
import clsx from 'clsx'
import { Upload, Image as ImageIcon, X } from 'lucide-react'

export default function ImageDropzone({ file, preview, onSelect, onClear }) {
  const inputRef = useRef(null)
  const [drag, setDrag] = useState(false)

  const pickFile = (f) => {
    if (!f || !f.type.startsWith('image/')) return
    onSelect(f)
  }

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDrag(false)
    pickFile(e.dataTransfer.files?.[0])
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onSelect])

  if (preview) {
    return (
      <div className="relative group rounded-2xl overflow-hidden border border-slate-200 bg-white">
        <img src={preview} alt="" className="w-full max-h-[420px] object-contain bg-slate-100" />
        <div className="absolute inset-x-0 bottom-0 px-4 py-2.5 bg-gradient-to-t from-black/60 via-black/40 to-transparent flex items-center justify-between">
          <div className="flex items-center gap-2 text-white/90 text-xs">
            <ImageIcon className="size-3.5" />
            <span className="truncate max-w-[24rem]">{file?.name}</span>
          </div>
          <button
            type="button"
            onClick={onClear}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-white/95 hover:bg-white text-slate-700 text-xs font-medium shadow-sm"
          >
            <X className="size-3.5" />
            Replace
          </button>
        </div>
      </div>
    )
  }

  return (
    <label
      htmlFor="image-input"
      onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
      className={clsx(
        'relative flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed cursor-pointer transition-all',
        'min-h-[280px] p-8 text-center',
        drag
          ? 'border-indigo-400 bg-indigo-50/60'
          : 'border-slate-300 bg-white hover:border-indigo-300 hover:bg-indigo-50/30',
      )}
    >
      <input
        ref={inputRef}
        id="image-input"
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => pickFile(e.target.files?.[0])}
      />
      <div className="size-14 rounded-2xl bg-gradient-to-br from-indigo-50 to-indigo-100 flex items-center justify-center text-indigo-600 shadow-inner">
        <Upload className="size-6" />
      </div>
      <div>
        <p className="font-medium text-slate-900">Drop an image, or click to browse</p>
        <p className="text-sm text-slate-500 mt-0.5">JPG / PNG / WebP — drone aerials work best</p>
      </div>
      <p className="text-[11px] text-slate-400 uppercase tracking-wider">
        Max 1 image per analysis
      </p>
    </label>
  )
}
