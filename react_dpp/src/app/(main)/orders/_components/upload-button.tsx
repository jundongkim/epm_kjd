"use client"

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { toast } from "sonner"
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Input } from "@/components/ui/input"

interface UploadButtonProps {
    onUploadSuccess: () => void;
}

export function UploadButton({ onUploadSuccess }: UploadButtonProps) {
    const [loading, setLoading] = useState(false);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [versionName, setVersionName] = useState("");
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            setVersionName(file.name); // 기본 버전 이름을 파일 이름으로 설정
            setDialogOpen(true); // 파일을 선택하면 다이얼로그 열기
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        setLoading(true);
        setDialogOpen(false);
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('versionName', versionName);

        try {
            const response = await fetch('/api/orders', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || '업로드에 실패했습니다.');
            }
            
            toast.success("파일이 성공적으로 업로드되었습니다.");
            onUploadSuccess();

        } catch (error: any) {
            console.error(error);
            toast.error(error.message || '업로드 중 오류가 발생했습니다.');
        } finally {
            setLoading(false);
            // Reset state
            setSelectedFile(null);
            setVersionName("");
            if(fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const handleButtonClick = () => {
        fileInputRef.current?.click();
    };

    return (
        <>
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".csv"
                style={{ display: 'none' }}
                disabled={loading}
            />
            <Button onClick={handleButtonClick} disabled={loading}>
                {loading ? '업로드 중...' : 'CSV 업로드'}
            </Button>

            <AlertDialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>버전 이름 설정</AlertDialogTitle>
                        <AlertDialogDescription>
                            업로드할 주문 데이터의 버전을 식별할 수 있는 이름을 입력해주세요.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <Input
                        value={versionName}
                        onChange={(e) => setVersionName(e.target.value)}
                        placeholder="예: 2024년 6월 확정 주문"
                    />
                    <AlertDialogFooter>
                        <AlertDialogCancel onClick={() => {
                            if(fileInputRef.current) fileInputRef.current.value = '';
                        }}>취소</AlertDialogCancel>
                        <AlertDialogAction onClick={handleUpload} disabled={!versionName.trim()}>
                            업로드
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
} 