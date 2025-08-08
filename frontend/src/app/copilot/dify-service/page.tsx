// Dify Service Page - AI Advisor 외부 기능용
// AI Advisor에서는 사용하지 않음

'use client'

import { useState, useEffect } from 'react'
import { Plus, Settings, Trash2, Edit, Check, X, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/use-toast'
import { useDify } from '@/hooks/useDify'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'

interface ServiceFormData {
  name: string
  baseUrl: string
  apiKey: string
}

export default function DifyServicePage() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [editingService, setEditingService] = useState<any>(null)
  const [deletingService, setDeletingService] = useState<any>(null)
  const [formData, setFormData] = useState<ServiceFormData>({
    name: '',
    baseUrl: '',
    apiKey: ''
  })
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)

  const { toast } = useToast()
  const {
    services,
    currentService,
    loading,
    error,
    createService,
    updateService,
    deleteService,
    setActiveService,
    testService
  } = useDify()

  const resetForm = () => {
    setFormData({
      name: '',
      baseUrl: '',
      apiKey: ''
    })
    setTestResult(null)
  }

  const handleCreate = async () => {
    try {
      await createService(formData)
      toast({
        title: "서비스 생성됨",
        description: "Dify 서비스가 성공적으로 생성되었습니다.",
      })
      setIsCreateDialogOpen(false)
      resetForm()
    } catch (error: any) {
      toast({
        title: "오류",
        description: error.message || "서비스 생성에 실패했습니다.",
        variant: "destructive",
      })
    }
  }

  const handleEdit = async () => {
    if (!editingService) return

    try {
      await updateService({
        id: editingService.id,
        ...formData
      })
      toast({
        title: "서비스 업데이트됨",
        description: "Dify 서비스가 성공적으로 업데이트되었습니다.",
      })
      setIsEditDialogOpen(false)
      setEditingService(null)
      resetForm()
    } catch (error: any) {
      toast({
        title: "오류",
        description: error.message || "서비스 업데이트에 실패했습니다.",
        variant: "destructive",
      })
    }
  }

  const handleDelete = async () => {
    if (!deletingService) return

    try {
      await deleteService(deletingService.id)
      toast({
        title: "서비스 삭제됨",
        description: "Dify 서비스가 성공적으로 삭제되었습니다.",
      })
      setIsDeleteDialogOpen(false)
      setDeletingService(null)
    } catch (error: any) {
      toast({
        title: "오류",
        description: error.message || "서비스 삭제에 실패했습니다.",
        variant: "destructive",
      })
    }
  }

  const handleTest = async () => {
    setIsTesting(true)
    setTestResult(null)

    try {
      const result = await testService(formData)
      setTestResult(result)
      
      if (result.success) {
        toast({
          title: "연결 성공",
          description: `서비스에 성공적으로 연결되었습니다. (${result.appsCount}개 앱 발견)`,
        })
      } else {
        toast({
          title: "연결 실패",
          description: result.message,
          variant: "destructive",
        })
      }
    } catch (error: any) {
      toast({
        title: "테스트 오류",
        description: error.message || "서비스 테스트에 실패했습니다.",
        variant: "destructive",
      })
    } finally {
      setIsTesting(false)
    }
  }

  const openEditDialog = (service: any) => {
    setEditingService(service)
    setFormData({
      name: service.name,
      baseUrl: service.baseUrl,
      apiKey: service.apiKey
    })
    setIsEditDialogOpen(true)
  }

  const openDeleteDialog = (service: any) => {
    setDeletingService(service)
    setIsDeleteDialogOpen(true)
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dify 서비스 관리</h1>
          <p className="text-muted-foreground">
            Dify AI 플랫폼 서비스를 관리하고 설정합니다.
          </p>
        </div>
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          새 서비스 추가
        </Button>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-red-600" />
              <span className="text-red-800">{error.message}</span>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4">
        {services.map((service) => (
          <Card key={service.id} className="hover:shadow-md transition-shadow">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <Settings className="w-5 h-5" />
                    <div>
                      <h3 className="font-semibold">{service.name}</h3>
                      <p className="text-sm text-muted-foreground">{service.baseUrl}</p>
                    </div>
                  </div>
                  {service.isActive && (
                    <Badge variant="default">활성</Badge>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  {!service.isActive && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setActiveService(service.id)}
                    >
                      활성화
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openEditDialog(service)}
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openDeleteDialog(service)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {services.length === 0 && !loading && (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <Settings className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">서비스가 없습니다</h3>
                <p className="text-muted-foreground mb-4">
                  첫 번째 Dify 서비스를 추가해보세요.
                </p>
                <Button onClick={() => setIsCreateDialogOpen(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  서비스 추가
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Create Service Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>새 Dify 서비스 추가</DialogTitle>
            <DialogDescription>
              Dify 서비스의 연결 정보를 입력하세요.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">서비스 이름</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="My Dify Service"
              />
            </div>
            <div>
              <Label htmlFor="baseUrl">기본 URL</Label>
              <Input
                id="baseUrl"
                value={formData.baseUrl}
                onChange={(e) => setFormData({ ...formData, baseUrl: e.target.value })}
                placeholder="http://localhost:5001"
              />
            </div>
            <div>
              <Label htmlFor="apiKey">API 키</Label>
              <Input
                id="apiKey"
                type="password"
                value={formData.apiKey}
                onChange={(e) => setFormData({ ...formData, apiKey: e.target.value })}
                placeholder="sk-..."
              />
            </div>
            {testResult && (
              <div className={`p-3 rounded-md ${
                testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
              }`}>
                <div className="flex items-center space-x-2">
                  {testResult.success ? (
                    <Check className="w-4 h-4 text-green-600" />
                  ) : (
                    <X className="w-4 h-4 text-red-600" />
                  )}
                  <span className={testResult.success ? 'text-green-800' : 'text-red-800'}>
                    {testResult.message}
                  </span>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={handleTest}
              disabled={isTesting || !formData.name || !formData.baseUrl || !formData.apiKey}
            >
              {isTesting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  테스트 중...
                </>
              ) : (
                '연결 테스트'
              )}
            </Button>
            <Button onClick={handleCreate} disabled={loading || !formData.name || !formData.baseUrl || !formData.apiKey}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  생성 중...
                </>
              ) : (
                '서비스 생성'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Service Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>서비스 편집</DialogTitle>
            <DialogDescription>
              Dify 서비스 정보를 수정하세요.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="edit-name">서비스 이름</Label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="My Dify Service"
              />
            </div>
            <div>
              <Label htmlFor="edit-baseUrl">기본 URL</Label>
              <Input
                id="edit-baseUrl"
                value={formData.baseUrl}
                onChange={(e) => setFormData({ ...formData, baseUrl: e.target.value })}
                placeholder="http://localhost:5001"
              />
            </div>
            <div>
              <Label htmlFor="edit-apiKey">API 키</Label>
              <Input
                id="edit-apiKey"
                type="password"
                value={formData.apiKey}
                onChange={(e) => setFormData({ ...formData, apiKey: e.target.value })}
                placeholder="sk-..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleEdit} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  업데이트 중...
                </>
              ) : (
                '업데이트'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Service Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>서비스 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              "{deletingService?.name}" 서비스를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-red-600 hover:bg-red-700">
              삭제
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
