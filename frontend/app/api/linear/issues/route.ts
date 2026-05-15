import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { apolloClient } from "@/lib/apollo-client";
import { gql } from "@apollo/client";

const GET_ISSUES = gql`
  query GetIssues($projectId: String!, $first: Int = 50) {
    project(id: $projectId) {
      id
      name
      issues(first: $first) {
        nodes {
          id
          title
          description
          priority
          estimate
          state {
            id
            name
            type
          }
          assignee {
            id
            name
            email
          }
          createdAt
          updatedAt
          dueDate
          labels {
            nodes {
              id
              name
              color
            }
          }
        }
      }
    }
  }
`;

export async function GET(request: NextRequest) {
  try {
    const session = await auth();

    if (!session) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get("projectId");

    if (!projectId) {
      return NextResponse.json(
        { error: "projectId is required" },
        { status: 400 }
      );
    }

    const { data, errors } = await apolloClient.query({
      query: GET_ISSUES,
      variables: { projectId },
      context: {
        headers: {
          "X-Tenant-ID": session.user.tenantId,
        },
      },
    });

    if (errors) {
      console.error("Linear API errors:", errors);
      return NextResponse.json(
        { error: "Failed to fetch issues", details: errors },
        { status: 500 }
      );
    }

    return NextResponse.json({
      project: data.project,
      issues: data.project?.issues?.nodes || [],
    });
  } catch (error) {
    console.error("Error fetching Linear issues:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
