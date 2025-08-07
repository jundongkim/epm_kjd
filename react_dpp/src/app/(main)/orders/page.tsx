import { Order, OrderVersion } from "@prisma/client";
import { DataTable } from "./_components/data-table";
import { columns } from "./_components/columns";
import prisma from "@/lib/prisma";

// 1. 모든 OrderVersion 목록을 가져오는 함수
async function getOrderVersions(): Promise<OrderVersion[]> {
  const versions = await prisma.orderVersion.findMany({
    orderBy: {
      createdAt: 'desc'
    }
  });
  return versions;
}

// 2. 특정 버전 또는 최신 버전의 Order 목록을 가져오는 함수
async function getOrders(versionId?: number): Promise<Order[]> {
  let whereClause: { orderVersionId?: number } = {};

  if (versionId) {
    whereClause.orderVersionId = versionId;
  } else {
    const latestVersion = await prisma.orderVersion.findFirst({
      orderBy: { createdAt: 'desc' },
    });
    if (latestVersion) {
      whereClause.orderVersionId = latestVersion.id;
    } else {
      return []; // 버전이 없으면 빈 배열 반환
    }
  }

  const orders = await prisma.order.findMany({
    where: whereClause,
    orderBy: {
      id: 'asc'
    }
  });
  return orders;
}

export default async function OrdersPage({
  searchParams,
}: {
  searchParams: { [key: string]: string | string[] | undefined };
}) {
  const versionId =
    typeof searchParams.version === 'string' ? parseInt(searchParams.version, 10) : undefined;
  
  // 3. 데이터 로딩 함수 병렬 실행
  const [orders, versions] = await Promise.all([
    getOrders(versionId),
    getOrderVersions()
  ]);

  const selectedVersion = 
    versionId 
    ? versions.find(v => v.id === versionId) 
    : (versions[0] || null);

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-2xl font-bold mb-4">
        주문 확인 - {selectedVersion ? selectedVersion.name : "데이터 없음"}
      </h1>
      <DataTable 
        columns={columns} 
        data={orders}
        versions={versions} // 버전 목록 전달
        selectedVersionId={selectedVersion?.id} // 선택된 버전 ID 전달
      />
    </div>
  );
} 