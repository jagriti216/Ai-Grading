import { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { FileUp, File, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function FileUpload({ label, file, setFile, acceptDescription = 'PDF documents only (up to 10MB)' }) {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isSimulating, setIsSimulating] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      const selected = acceptedFiles[0];
      setFile(selected);
      setIsSimulating(true);
      setUploadProgress(0);
    }
  }, [setFile]);

  useEffect(() => {
    let interval;
    if (isSimulating && file) {
      interval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval);
            setIsSimulating(false);
            return 100;
          }
          return prev + 10;
        });
      }, 50);
    }
    return () => clearInterval(interval);
  }, [isSimulating, file]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: isSimulating,
  });

  const removeFile = (e) => {
    e.stopPropagation();
    setFile(null);
    setUploadProgress(0);
    setIsSimulating(false);
  };

  return (
    <div className="space-y-2">
      {label && <label className="block text-sm font-semibold text-slate-700">{label}</label>}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 relative overflow-hidden ${
          file
            ? 'border-indigo-200 bg-indigo-50/20'
            : isDragActive
            ? 'border-indigo-500 bg-indigo-50/40 scale-[1.02] shadow-card-hover'
            : isDragReject
            ? 'border-rose-500 bg-rose-50/30'
            : 'border-slate-200 hover:border-indigo-400 bg-white hover:bg-indigo-50/10 hover:shadow-card'
        }`}
      >
        <input {...getInputProps()} />
        <AnimatePresence mode="wait">
          {file ? (
            <motion.div
              key="file-details"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4"
            >
              <div className="flex items-center justify-between p-3 bg-white rounded-xl shadow-sm border border-slate-100">
                <div className="flex items-center space-x-3 text-left min-w-0">
                  <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600 shrink-0">
                    <File className="h-6 w-6" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-900 truncate">{file.name}</p>
                    <p className="text-xs text-slate-400">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={removeFile}
                  aria-label="Remove file"
                  className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-all active:scale-90 min-h-[44px] min-w-[44px] flex items-center justify-center"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-1 text-left">
                <div className="flex justify-between text-xs font-semibold text-slate-500">
                  <span>{uploadProgress === 100 ? 'Ready to upload' : 'Reading file...'}</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-indigo-600 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${uploadProgress}%` }}
                    transition={{ duration: 0.2 }}
                  />
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="dropzone-prompt"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              <div className={`mx-auto w-12 h-12 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 transition-transform duration-300 ${isDragActive ? 'scale-110' : ''}`}>
                <FileUp className="h-6 w-6" />
              </div>
              <div className="text-slate-600 text-sm">
                <span className="font-semibold text-indigo-600">Click to upload</span> or drag and drop
              </div>
              <p className="text-xs text-slate-400 font-medium">{acceptDescription}</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
