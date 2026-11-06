import React, { useState, useCallback } from 'react';

import { useTranslation } from 'react-i18next';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {

  Upload,

  File,

  FileText,

  X,

  Check,

  AlertCircle,

  Loader2

} from 'lucide-react';

import { documentsService } from '../services/documents.service';

import { Card } from '../components/ui/Card';

import { Button } from '../components/ui/Button';

import { EmptyState } from '../components/ui/EmptyState';

import type { DocumentRead } from '../types/api';



export const DocumentsPage: React.FC = () => {

  const { t } = useTranslation();

  const queryClient = useQueryClient();

  const [dragActive, setDragActive] = useState(false);

  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});



  // Fetch documents (mocked for now since list endpoint doesn't exist)

  const [documents, setDocuments] = useState<DocumentRead[]>([]);



  const uploadMutation = useMutation({

    mutationFn: (file: File) => documentsService.upload(file),

    onSuccess: (response, file) => {

      // Add to local list

      const newDoc: DocumentRead = {

        id: response.document_id,

        user_id: '',

        document_type: response.document_type,

        original_filename: response.original_filename,

        mime_type: undefined,

        size_bytes: response.size_bytes,

        created_at: new Date().toISOString(),

        assessment: {

          extracted_fields: {},

          missing_fields: [],

          dates_to_check: [],

          notes: [],

          is_genuine: null,

          redacted: false,

        },

      };

      setDocuments((prev) => [newDoc, ...prev]);

      delete uploadProgress[file.name];

      setUploadProgress({ ...uploadProgress });

    },

    onError: (error, file) => {

      console.error('Upload failed:', error);

      delete uploadProgress[file.name];

      setUploadProgress({ ...uploadProgress });

    },

  });



  const handleFileSelect = (files: FileList | null) => {

    if (!files) return;



    Array.from(files).forEach((file) => {

      // Validate file

      const maxSize = 10 * 1024 * 1024; // 10MB

      if (file.size > maxSize) {

        alert(t('documents.fileTooLarge', { defaultValue: 'File too large. Max 10MB.' }));

        return;

      }



      // Start upload

      setUploadProgress((prev) => ({ ...prev, [file.name]: 0 }));

      uploadMutation.mutate(file);

    });

  };



  const handleDrag = useCallback((e: React.DragEvent) => {

    e.preventDefault();

    e.stopPropagation();

    if (e.type === 'dragenter' || e.type === 'dragover') {

      setDragActive(true);

    } else if (e.type === 'dragleave') {

      setDragActive(false);

    }

  }, []);



  const handleDrop = useCallback((e: React.DragEvent) => {

    e.preventDefault();

    e.stopPropagation();

    setDragActive(false);



    if (e.dataTransfer.files) {

      handleFileSelect(e.dataTransfer.files);

    }

  }, []);



  const handleDeleteDocument = (docId: string) => {

    if (confirm(t('documents.confirmDelete', { defaultValue: 'Delete this document?' }))) {

      documentsService.delete(docId).then(() => {

        setDocuments((prev) => prev.filter((d) => d.id !== docId));

      });

    }

  };



  const acceptedTypes = '.pdf,.jpg,.jpeg,.png,.doc,.docx';



  return (

    <div className="max-w-6xl mx-auto space-y-6">

      {/* Header */}

      <div>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">{t('documents.title')}</h1>

        <p className="text-gray-600">

          {t('documents.description', {

            defaultValue: 'Upload and manage your documents for government scheme applications.'

          })}

        </p>

      </div>



      {/* Upload Area */}

      <Card className="p-6">

        <div

          onDragEnter={handleDrag}

          onDragLeave={handleDrag}

          onDragOver={handleDrag}

          onDrop={handleDrop}

          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${

            dragActive

              ? 'border-indigo-500 bg-indigo-50'

              : 'border-gray-300 hover:border-indigo-400'

          }`}

        >

          <div className="flex flex-col items-center gap-4">

            <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center">

              <Upload className="h-8 w-8 text-indigo-600" />

            </div>

            <div>

              <p className="text-lg font-semibold text-gray-900 mb-1">

                {t('documents.dropFiles', { defaultValue: 'Drop files here' })}

              </p>

              <p className="text-sm text-gray-600 mb-4">

                {t('documents.orClickBrowse', { defaultValue: 'or click to browse' })}

              </p>

              <label className="inline-block">

                <input

                  type="file"

                  multiple

                  accept={acceptedTypes}

                  onChange={(e) => handleFileSelect(e.target.files)}

                  className="hidden"

                />

                <span className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none bg-primary text-primary-foreground hover:bg-primary/90 h-10 py-2 px-4 cursor-pointer">

                  {t('documents.selectFiles', { defaultValue: 'Select Files' })}

                </span>

              </label>

            </div>

            <div className="text-xs text-gray-500">

              {t('documents.acceptedFormats', {

                defaultValue: 'PDF, JPG, PNG, DOC (Max 10MB each)'

              })}

            </div>

          </div>

        </div>



        {/* Upload Progress */}

        {Object.keys(uploadProgress).length > 0 && (

          <div className="mt-4 space-y-2">

            {Object.entries(uploadProgress).map(([filename, progress]) => (

              <div key={filename} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">

                <Loader2 className="h-4 w-4 text-indigo-600 animate-spin flex-shrink-0" />

                <div className="flex-1 min-w-0">

                  <p className="text-sm font-medium text-gray-900 truncate">{filename}</p>

                  <p className="text-xs text-gray-500">

                    {t('documents.uploading', { defaultValue: 'Uploading...' })}

                  </p>

                </div>

              </div>

            ))}

          </div>

        )}

      </Card>



      {/* Documents List */}

      {documents.length > 0 ? (

        <div>

          <h2 className="text-xl font-semibold text-gray-900 mb-4">

            {t('documents.uploadedDocuments', { defaultValue: 'Uploaded Documents' })}

          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

            {documents.map((doc) => (

              <Card key={doc.id} className="p-4 hover:shadow-md transition-shadow">

                <div className="flex items-start gap-3">

                  <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center flex-shrink-0">

                    <FileText className="h-5 w-5 text-indigo-600" />

                  </div>

                  <div className="flex-1 min-w-0">

                    <p className="font-medium text-gray-900 truncate text-sm">

                      {doc.original_filename}

                    </p>

                    <p className="text-xs text-gray-500 mt-1">

                      {(doc.size_bytes / 1024).toFixed(1)} KB

                    </p>

                    <div className="flex items-center gap-1 mt-2">

                      <Check className="h-3 w-3 text-green-600" />

                      <span className="text-xs text-green-700">

                        {t('documents.uploaded', { defaultValue: 'Uploaded' })}

                      </span>

                    </div>

                  </div>

                  <button

                    onClick={() => handleDeleteDocument(doc.id)}

                    className="p-1 hover:bg-red-50 rounded transition-colors"

                    aria-label="Delete"

                  >

                    <X className="h-4 w-4 text-red-600" />

                  </button>

                </div>

                <div className="mt-3 pt-3 border-t border-gray-100">

                  <p className="text-xs text-gray-500">

                    {t('documents.type', { defaultValue: 'Type' })}: {doc.document_type}

                  </p>

                </div>

              </Card>

            ))}

          </div>

        </div>

      ) : (

        <Card className="p-8">

          <EmptyState

            icon={File}

            title={t('documents.noDocuments', { defaultValue: 'No documents uploaded' })}

            description={t('documents.noDocumentsDesc', {

              defaultValue: 'Upload documents to keep them organized for your applications.'

            })}

          />

        </Card>

      )}



      {/* Info Banner */}

      <Card className="bg-blue-50 border-blue-200 p-4">

        <div className="flex gap-3">

          <AlertCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />

          <div className="text-sm">

            <p className="font-medium text-blue-900 mb-1">

              {t('documents.securityTitle', { defaultValue: 'Your documents are secure' })}

            </p>

            <p className="text-blue-700">

              {t('documents.securityDesc', {

                defaultValue: 'All uploads are encrypted and stored securely. We never share your documents without permission.'

              })}

            </p>

          </div>

        </div>

      </Card>

    </div>

  );

};
