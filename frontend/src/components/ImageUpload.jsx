import { useState } from 'react'

export default function ImageUpload({ onPredict, loading }) {
  const [selectedImage, setSelectedImage] = useState(null)
  const [preview, setPreview] = useState(null)

  const handleImageChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedImage(file)
      setPreview(URL.createObjectURL(file))
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (selectedImage) {
      onPredict(selectedImage)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-indigo-500 transition">
        <input
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          className="hidden"
          id="imageInput"
        />
        <label htmlFor="imageInput" className="cursor-pointer">
          <div className="text-gray-600">
            <svg className="mx-auto h-12 w-12 mb-4" stroke="currentColor" fill="none" viewBox="0 0 48 48">
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <p className="text-lg">Click to upload image</p>
          </div>
        </label>
      </div>

      {preview && (
        <div className="mt-4">
          <img src={preview} alt="Preview" className="max-h-64 mx-auto rounded-lg shadow-md" />
        </div>
      )}

      <button
        type="submit"
        disabled={!selectedImage || loading}
        className="w-full bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
      >
        {loading ? 'Analyzing...' : 'Detect Disaster'}
      </button>
    </form>
  )
}
