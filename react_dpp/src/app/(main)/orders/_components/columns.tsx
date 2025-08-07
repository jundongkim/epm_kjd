"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Order } from "@prisma/client"
import { ArrowUpDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { CellAction } from "./cell-action"

export const columns: ColumnDef<Order>[] = [
  {
    accessorKey: "division",
    header: "구분",
  },
  {
    accessorKey: "team",
    header: "팀",
  },
  {
    accessorKey: "customer_name",
    header: "고객명",
  },
  {
    accessorKey: "steel_grade_ordered",
    header: "강종(주문)",
    cell: ({ row }) => (
      <div className="font-bold text-sky-500">
        {row.getValue("steel_grade_ordered")}
      </div>
    ),
  },
  {
    accessorKey: "steel_grade_produced",
    header: "강종(생산)",
  },
  {
    accessorKey: "code",
    header: "코드",
  },
  {
    accessorKey: "steel_plant",
    header: "제강공장",
  },
  {
    accessorKey: "code2",
    header: "코드2",
  },
  {
    accessorKey: "rolling",
    header: "압연",
  },
  {
    accessorKey: "thickness",
    header: "두께",
    cell: ({ row }) => (
      <div className="font-bold text-sky-500">{row.getValue("thickness")}</div>
    ),
  },
  {
    accessorKey: "product_length",
    header: "길이(제품)",
    cell: ({ row }) => (
      <div className="font-bold text-sky-500">
        {row.getValue("product_length")}
      </div>
    ),
  },
  {
    accessorKey: "material_length",
    header: "길이(소재)",
  },
  {
    accessorKey: "requested_quantity",
    header: "요청량",
  },
  {
    accessorKey: "stock_quantity",
    header: "재고량",
  },
  {
    accessorKey: "steelmaking_quantity",
    header: "제강량",
  },
  {
    accessorKey: "ch_count",
    header: "Ch수",
  },
  {
    accessorKey: "final_production_quantity",
    header: "생산량(최종)",
    cell: ({ row }) => (
      <div className="font-bold text-sky-500">
        {row.getValue("final_production_quantity")}
      </div>
    ),
  },
  {
    accessorKey: "usage",
    header: "용도별",
  },
  {
    accessorKey: "adjusted_quantity",
    header: "조정량",
  },
  {
    accessorKey: "carryover_order",
    header: "이월주문",
  },
  {
    accessorKey: "small_lot_classification",
    header: "소LOT분류",
  },
  {
    accessorKey: "production_increase_review",
    header: "생산증량 검토 시",
  },
  {
    accessorKey: "remarks_factory",
    header: "비고(공장)",
  },
  {
    accessorKey: "remarks_sales",
    header: "비고(영업) - 특기사항",
  },
  {
    accessorKey: "remarks",
    header: "비고",
  },
  {
    accessorKey: "requested_line",
    header: "요청라인",
  },
  {
    id: "actions",
    cell: ({ row }) => <CellAction data={row.original} />,
  },
] 