import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { apolloClient } from "@/lib/apollo-client";
import { gql } from "@apollo/client";

const GET_PROJECTS = gql`
  query GetProjects($teamId: String!) {
    team(id: $teamId) {
      id
      name
      projects(first: 50) {
        nodes {
          id
          name
          description
          state
          progress
          startedAt
          targetDate
          lead {
            id
            name
            email
          }
          members {
            nodes {
              id
              name
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

    const tenantId = session.user.tenantId;

    // Get teamId from query params or use tenantId as default
    const { searchParams } = new URL(request.url);
    const teamId = searchParams.get("teamId") || tenantId;

    const { data, errors } = await apolloClient.query({
      query: GET_PROJECTS,
      variables: { teamId },
      context: {
        headers: {
          "X-Tenant-ID": tenantId,
        },
      },
    });

    if (errors) {
      console.error("Linear API errors:", errors);
      return NextResponse.json(
        { error: "Failed to fetch projects", details: errors },
        { status: 500 }
      );
    }

    return NextResponse.json({
      team: data.team,
      projects: data.team?.projects?.nodes || [],
    });
  } catch (error) {
    console.error("Error fetching Linear projects:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
