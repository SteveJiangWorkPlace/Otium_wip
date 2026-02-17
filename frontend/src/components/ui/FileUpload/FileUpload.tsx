import React, { useState, useRef, useCallback } from 'react';
import { Icon, Button } from '../index';
import styles from './FileUpload.module.css';

export interface UploadedFile {
  id: string;
  file: File;
  previewUrl?: string;
  error?: string;
}

export interface FileUploadProps {
  acceptedTypes?: string;
  maxSize?: number; // in bytes
  maxFiles?: number;
  onFilesChange?: (files: UploadedFile[]) => void;
  disabled?: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({
  acceptedTypes = 'image/*,.pdf',
  maxSize = 10 * 1024 * 1024, // 10MB
  maxFiles = 10,
  onFilesChange,
  disabled = false,
}) => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 验证文件类型
  const isValidFileType = useCallback(
    (file: File): boolean => {
      if (!acceptedTypes) return true;

      const acceptedExtensions = acceptedTypes.split(',').map((ext) => ext.trim().toLowerCase());

      // 检查MIME类型
      if (acceptedExtensions.includes(file.type.toLowerCase())) {
        return true;
      }

      // 检查文件扩展名
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      if (fileExtension && acceptedExtensions.includes(fileExtension)) {
        return true;
      }

      // 检查通配符模式
      if (acceptedExtensions.includes('image/*') && file.type.startsWith('image/')) {
        return true;
      }

      return false;
    },
    [acceptedTypes]
  );

  // 验证文件大小
  const isValidFileSize = useCallback(
    (file: File): boolean => {
      return file.size <= maxSize;
    },
    [maxSize]
  );

  // 处理文件选择
  const handleFileSelect = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;

      setUploadError(null);

      const newUploadedFiles: UploadedFile[] = [];
      const errors: string[] = [];

      // 检查文件数量限制
      const totalFiles = uploadedFiles.length + files.length;
      if (totalFiles > maxFiles) {
        setUploadError(`最多只能上传 ${maxFiles} 个文件`);
        return;
      }

      Array.from(files).forEach((file, index) => {
        // 验证文件类型
        if (!isValidFileType(file)) {
          errors.push(`${file.name}: 不支持的文件类型`);
          return;
        }

        // 验证文件大小
        if (!isValidFileSize(file)) {
          const maxSizeMB = (maxSize / (1024 * 1024)).toFixed(1);
          errors.push(`${file.name}: 文件大小超过 ${maxSizeMB}MB 限制`);
          return;
        }

        // 生成预览URL
        let previewUrl: string | undefined;
        if (file.type.startsWith('image/')) {
          previewUrl = URL.createObjectURL(file);
        }

        const uploadedFile: UploadedFile = {
          id: `${Date.now()}-${index}`,
          file,
          previewUrl,
        };

        newUploadedFiles.push(uploadedFile);
      });

      if (errors.length > 0) {
        setUploadError(errors.join(', '));
      }

      if (newUploadedFiles.length > 0) {
        const updatedFiles = [...uploadedFiles, ...newUploadedFiles];
        setUploadedFiles(updatedFiles);
        onFilesChange?.(updatedFiles);
      }
    },
    [uploadedFiles, maxFiles, maxSize, onFilesChange, isValidFileSize, isValidFileType]
  );

  // 处理拖放
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (disabled) return;

      const files = e.dataTransfer.files;
      handleFileSelect(files);
    },
    [disabled, handleFileSelect]
  );

  // 处理文件输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files);

    // 重置input值，允许再次选择相同文件
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 删除文件
  const handleDeleteFile = (id: string) => {
    const fileToDelete = uploadedFiles.find((f) => f.id === id);

    // 释放预览URL占用的内存
    if (fileToDelete?.previewUrl) {
      URL.revokeObjectURL(fileToDelete.previewUrl);
    }

    const updatedFiles = uploadedFiles.filter((f) => f.id !== id);
    setUploadedFiles(updatedFiles);
    onFilesChange?.(updatedFiles);
  };

  // 清理预览URL
  React.useEffect(() => {
    return () => {
      uploadedFiles.forEach((file) => {
        if (file.previewUrl) {
          URL.revokeObjectURL(file.previewUrl);
        }
      });
    };
  }, [uploadedFiles]);

  // 获取文件图标
  const getFileIcon = (fileType: string) => {
    if (fileType.startsWith('image/')) {
      return <Icon name="preview" size="sm" />;
    } else if (fileType === 'application/pdf') {
      return <Icon name="psReview" size="sm" />;
    }
    return <Icon name="download" size="sm" />;
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={styles.container}>
      {/* 拖放区域 */}
      <div
        className={`${styles.dropzone} ${isDragging ? styles.dragging : ''} ${disabled ? styles.disabled : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
      >
        <div className={styles.dropzoneContent}>
          <Icon name="download" size="lg" className={styles.dropzoneIcon} />
          <div className={styles.dropzoneText}>
            <p className={styles.dropzoneTitle}>点击或拖拽文件到这里上传</p>
            <p className={styles.dropzoneDescription}>
              支持图片和PDF文件，单个文件不超过 {formatFileSize(maxSize)}
            </p>
          </div>
          <Button
            variant="secondary"
            size="small"
            className={styles.browseButton}
            disabled={disabled}
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            选择文件
          </Button>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedTypes}
          onChange={handleInputChange}
          className={styles.fileInput}
          disabled={disabled}
        />
      </div>

      {/* 错误提示 */}
      {uploadError && (
        <div className={styles.error}>
          <Icon name="close" size="sm" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* 文件列表 */}
      {uploadedFiles.length > 0 && (
        <div className={styles.fileList}>
          <h3 className={styles.fileListTitle}>
            已上传文件 ({uploadedFiles.length}/{maxFiles})
          </h3>
          <div className={styles.fileItems}>
            {uploadedFiles.map((file) => (
              <div key={file.id} className={styles.fileItem}>
                <div className={styles.filePreview}>
                  {file.previewUrl ? (
                    <img src={file.previewUrl} alt={file.file.name} className={styles.fileImage} />
                  ) : (
                    <div className={styles.fileIcon}>{getFileIcon(file.file.type)}</div>
                  )}
                </div>

                <div className={styles.fileInfo}>
                  <div className={styles.fileName}>{file.file.name}</div>
                  <div className={styles.fileDetails}>
                    <span className={styles.fileType}>
                      {file.file.type.split('/')[1]?.toUpperCase() || '文件'}
                    </span>
                    <span className={styles.fileSize}>{formatFileSize(file.file.size)}</span>
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="small"
                  className={styles.deleteButton}
                  onClick={() => handleDeleteFile(file.id)}
                  aria-label={`删除 ${file.file.name}`}
                >
                  <Icon name="close" size="sm" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
